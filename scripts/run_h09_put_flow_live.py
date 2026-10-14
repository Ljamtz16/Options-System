#!/usr/bin/env python3
from __future__ import annotations

import fcntl
import json
import time
from datetime import date, datetime, timezone
from pathlib import Path

from options_system.chain_features import extract_chain_features
from options_system.h09_put_flow import VERSION, active_candidates, is_new_episode, live_delta_row
from options_system.intraday_contracts import representative_contracts
from options_system.session_cache import atomic_text

ROOT = Path(__file__).resolve().parents[1]
CFG = ROOT / "config/h09_put_flow_shadow_v01.json"
INDEX = ROOT / "data/raw/prospective/index.jsonl"
STATE = ROOT / "artifacts/intraday/H09_PUT_FLOW_LIVE_STATE_V01.json"
EVENTS = ROOT / "artifacts/intraday/H09_PUT_FLOW_LIVE_EVENTS_V01.jsonl"
LOCK = ROOT / "artifacts/intraday/.h09_put_flow_live.lock"
LOOP_SECONDS = 15


def now_iso(): return datetime.now(timezone.utc).isoformat()

def load_cfg(): return json.loads(CFG.read_text(encoding="utf-8"))

def initial_state(cfg):
    return {
        "version": VERSION,
        "policy_version": cfg["version"],
        "mode": "LIVE_SHADOW_NO_ORDERS",
        "paper_only": True,
        "broker_orders_enabled": False,
        "prospective_start_after": cfg["prospective_start_after"],
        "live_start_utc": now_iso(),
        "index_offset": INDEX.stat().st_size if INDEX.exists() else 0,
        "session_date": None,
        "previous_features": None,
        "last_signal_by_candidate": {},
        "signals": [],
        "counters": {"snapshots_processed": 0, "candidate_activations": 0, "episodes": 0},
        "updated_at_utc": now_iso(),
    }

def save(state):
    state["updated_at_utc"] = now_iso()
    atomic_text(STATE, json.dumps(state, indent=2) + "\n")

def event(payload):
    EVENTS.parent.mkdir(parents=True, exist_ok=True)
    with EVENTS.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"logged_at_utc": now_iso(), **payload}, sort_keys=True) + "\n")

def load_state(cfg):
    if not STATE.exists():
        state = initial_state(cfg); save(state); return state
    state = json.loads(STATE.read_text(encoding="utf-8"))
    if state.get("policy_version") != cfg["version"]:
        raise RuntimeError("H09_POLICY_VERSION_MISMATCH_FAIL_CLOSED")
    return state

def base_row(envelope):
    payload = envelope["payload"]
    captured = envelope["captured_at_utc"]
    research = payload.get("research_state") or {}
    features = research.get("features") or {}
    day = str(features.get("decision_date") or "")
    if not day:
        raise ValueError("H09 snapshot missing decision_date")
    underlying = (payload.get("underlying") or {}).get("snapshot") or {}
    trade = underlying.get("latestTrade") or {}
    quote = underlying.get("latestQuote") or {}
    spot = trade.get("p")
    if not spot and quote.get("bp") and quote.get("ap"):
        spot = (float(quote["bp"]) + float(quote["ap"])) / 2
    if not spot:
        raise ValueError("H09 snapshot missing SPY spot")
    chain = (payload.get("options") or {}).get("snapshot") or {}
    row = {
        "captured_at_utc": captured,
        "decision_date": day,
        "spot": float(spot),
    }
    row.update(extract_chain_features(chain, float(spot), date.fromisoformat(day)))
    row.update(((payload.get("cross_market") or {}).get("features") or {}))
    put = representative_contracts(chain, date.fromisoformat(day)).get("put")
    if put:
        row.update({
            "put_contract": put.get("symbol"), "put_entry_bid": put.get("bid"), "put_entry_ask": put.get("ask"),
            "put_entry_bid_size": put.get("bid_size"), "put_entry_ask_size": put.get("ask_size"),
        })
    return row

def process_snapshot(state, envelope, cfg):
    row = base_row(envelope)
    day = row["decision_date"]
    if day <= cfg["prospective_start_after"]:
        return
    if state.get("session_date") != day:
        state["session_date"] = day
        state["previous_features"] = None
        state["last_signal_by_candidate"] = {}
        event({"event": "SESSION_RESET", "decision_date": day})
    row = live_delta_row(state.get("previous_features"), row)
    state["previous_features"] = {k: row.get(k) for k in ("atm_iv", "put_call_iv_skew", "put_call_volume_ratio_1pct")}
    for cid in active_candidates(cfg, row):
        state["counters"]["candidate_activations"] += 1
        last = state["last_signal_by_candidate"].get(cid)
        if not is_new_episode(last, row["captured_at_utc"], cfg["episode_gap_minutes"]):
            continue
        state["last_signal_by_candidate"][cid] = row["captured_at_utc"]
        signal = {
            "signal_id": f"{cid}:{row['captured_at_utc']}", "candidate_id": cid, "side": "PUT",
            "decision_date": day, "signal_time": row["captured_at_utc"], "spot": row.get("spot"),
            "contract": row.get("put_contract"), "entry_bid": row.get("put_entry_bid"), "entry_ask": row.get("put_entry_ask"),
            "d_atm_iv_prev": row.get("d_atm_iv_prev"), "d_put_call_iv_skew_prev": row.get("d_put_call_iv_skew_prev"),
            "d_put_call_volume_ratio_1pct_prev": row.get("d_put_call_volume_ratio_1pct_prev"),
            "spy_from_open": row.get("spy_from_open"), "qqq_from_open": row.get("qqq_from_open"), "iwm_from_open": row.get("iwm_from_open"),
            "prospective_observation": True, "validated": False, "broker_order": False,
        }
        state["signals"].append(signal)
        state["counters"]["episodes"] += 1
        event({"event": "H09_SIGNAL", **signal})
    state["counters"]["snapshots_processed"] += 1
    state["last_processed_snapshot_utc"] = row["captured_at_utc"]

def process_index(state, cfg):
    if not INDEX.exists(): return 0
    count = 0
    with INDEX.open("rb") as f:
        offset = int(state.get("index_offset") or 0)
        size = INDEX.stat().st_size
        if offset > size: raise RuntimeError("H09_INDEX_TRUNCATED_FAIL_CLOSED")
        f.seek(offset)
        while True:
            raw = f.readline()
            if not raw: break
            nxt = f.tell()
            if not raw.strip(): state["index_offset"] = nxt; continue
            ref = json.loads(raw.decode("utf-8"))
            p = Path(ref["path"]); p = p if p.is_absolute() else ROOT / p
            if not p.exists(): break
            env = json.loads(p.read_text(encoding="utf-8"))
            if ref.get("sha256") and env.get("sha256") != ref["sha256"]: raise RuntimeError("H09_SNAPSHOT_SHA_MISMATCH")
            process_snapshot(state, env, cfg)
            state["index_offset"] = nxt; count += 1; save(state)
    return count

def main():
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    with LOCK.open("a+") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        cfg = load_cfg(); state = load_state(cfg)
        print(f"H09_LIVE_STARTED offset={state['index_offset']} mode={state['mode']}", flush=True)
        while True:
            n = process_index(state, cfg)
            if n: print(f"H09_LIVE_OK new={n} signals={len(state['signals'])}", flush=True)
            time.sleep(LOOP_SECONDS)

if __name__ == "__main__": main()
