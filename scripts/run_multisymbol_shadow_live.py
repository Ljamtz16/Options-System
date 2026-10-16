#!/usr/bin/env python3
from __future__ import annotations

import fcntl
import json
import time
from datetime import date, datetime, timezone
from pathlib import Path

from options_system.intraday_contracts import representative_contracts
from options_system.multisymbol_shadow import VERSION, active_candidates, derive_row, is_new_episode, signal_key
from options_system.session_cache import atomic_text

ROOT = Path(__file__).resolve().parents[1]
CFG = ROOT / "config/multisymbol_shadow_v01.json"
INDEX = ROOT / "data/raw/intraday/index.jsonl"
STATE = ROOT / "artifacts/intraday/MULTISYMBOL_LIVE_STATE_V01.json"
EVENTS = ROOT / "artifacts/intraday/MULTISYMBOL_LIVE_EVENTS_V01.jsonl"
LOCK = ROOT / "artifacts/intraday/.multisymbol_shadow_live.lock"
LOOP_SECONDS = 15


def now_iso(): return datetime.now(timezone.utc).isoformat()
def load_cfg(): return json.loads(CFG.read_text(encoding="utf-8"))

def initial_state(cfg):
    return {
        "version": VERSION, "policy_version": cfg["version"], "mode": "LIVE_SHADOW_NO_ORDERS",
        "broker_orders_enabled": False, "prospective_start_after": cfg["prospective_start_after"],
        "live_start_utc": now_iso(), "index_offset": INDEX.stat().st_size if INDEX.exists() else 0,
        "session_date": None, "first_spots": {}, "history": {}, "last_signal_by_candidate_symbol": {},
        "signals": [], "counters": {"snapshots_processed": 0, "symbol_rows": 0, "candidate_activations": 0, "episodes": 0},
        "updated_at_utc": now_iso(),
    }

def save(state):
    state["updated_at_utc"] = now_iso(); atomic_text(STATE, json.dumps(state, indent=2) + "\n")

def event(payload):
    EVENTS.parent.mkdir(parents=True, exist_ok=True)
    with EVENTS.open("a", encoding="utf-8") as f: f.write(json.dumps({"logged_at_utc": now_iso(), **payload}, sort_keys=True) + "\n")

def load_state(cfg):
    if not STATE.exists():
        s = initial_state(cfg); save(s); return s
    s = json.loads(STATE.read_text(encoding="utf-8"))
    if s.get("policy_version") != cfg["version"]: raise RuntimeError("MULTISYMBOL_POLICY_VERSION_MISMATCH_FAIL_CLOSED")
    return s

def base_symbol_row(envelope, symbol, rec):
    payload = envelope["payload"]; gc = payload.get("global_context") or {}; cross = gc.get("cross_market") or {}; vix = gc.get("vix") or {}
    return {
        "captured_at_utc": envelope["captured_at_utc"], "market_date": payload["market_date"], "symbol": symbol,
        "spot": rec.get("spot"), "market_spy_price": cross.get("spy_price"), "market_qqq_price": cross.get("qqq_price"),
        "market_iwm_price": cross.get("iwm_price"), "market_spy_from_open": cross.get("spy_from_open"),
        "market_qqq_from_open": cross.get("qqq_from_open"), "market_iwm_from_open": cross.get("iwm_from_open"),
        "vix_change_pct": vix.get("change_pct"),
    }

def process_snapshot(state, envelope, cfg):
    payload = envelope["payload"]; day = str(payload.get("market_date") or "")
    if not day or day <= cfg["prospective_start_after"]: return
    if state.get("session_date") != day:
        state["session_date"] = day; state["first_spots"] = {}; state["history"] = {}; state["last_signal_by_candidate_symbol"] = {}
        event({"event": "SESSION_RESET", "market_date": day})
    symbols = payload.get("symbols") or {}
    for core in ("SPY", "QQQ", "IWM"):
        if core in symbols: state["first_spots"].setdefault(core, float(symbols[core]["spot"]))
    market_first = {core: state["first_spots"].get(core) for core in ("SPY", "QQQ", "IWM")}
    for symbol, rec in symbols.items():
        if symbol not in cfg["symbols"]: continue
        spot = float(rec["spot"]); state["first_spots"].setdefault(symbol, spot)
        history = state["history"].setdefault(symbol, [])
        row = derive_row(base_symbol_row(envelope, symbol, rec), float(state["first_spots"][symbol]), history, market_first)
        for cand in active_candidates(cfg, row):
            state["counters"]["candidate_activations"] += 1
            event({
                "event": "MULTISYMBOL_ACTIVATION", "candidate_id": cand["id"], "side": cand["side"],
                "symbol": symbol, "market_date": day, "signal_time": row["captured_at_utc"],
                "own_from_first": row.get("own_from_first"), "own_return_5m": row.get("own_return_5m"),
                "market_spy_from_first": row.get("market_spy_from_first"), "market_qqq_from_first": row.get("market_qqq_from_first"),
                "market_iwm_from_first": row.get("market_iwm_from_first"), "broker_order": False,
            })
            key = signal_key(cand["id"], symbol); last = state["last_signal_by_candidate_symbol"].get(key)
            if not is_new_episode(last, row["captured_at_utc"], cfg["episode_gap_minutes"]): continue
            state["last_signal_by_candidate_symbol"][key] = row["captured_at_utc"]
            side = cand["side"].lower(); chain = rec.get("option_snapshot") or {}; rep = representative_contracts(chain, date.fromisoformat(day)).get(side)
            signal = {
                "signal_id": f"{cand['id']}:{symbol}:{row['captured_at_utc']}", "candidate_id": cand["id"], "side": cand["side"],
                "symbol": symbol, "market_date": day, "signal_time": row["captured_at_utc"], "spot": row.get("spot"),
                "own_from_first": row.get("own_from_first"), "own_return_5m": row.get("own_return_5m"), "relative_to_spy": row.get("relative_to_spy"),
                "market_spy_from_first": row.get("market_spy_from_first"), "market_qqq_from_first": row.get("market_qqq_from_first"),
                "market_iwm_from_first": row.get("market_iwm_from_first"), "vix_change_pct": row.get("vix_change_pct"),
                "contract": rep.get("symbol") if rep else None, "entry_bid": rep.get("bid") if rep else None, "entry_ask": rep.get("ask") if rep else None,
                "entry_bid_size": rep.get("bid_size") if rep else None, "entry_ask_size": rep.get("ask_size") if rep else None,
                "prospective_observation": True, "validated": False, "broker_order": False,
            }
            state["signals"].append(signal); state["counters"]["episodes"] += 1; event({"event": "MULTISYMBOL_SIGNAL", **signal})
        history.append({"captured_at_utc": row["captured_at_utc"], "spot": row["spot"]}); state["history"][symbol] = history[-8:]
        state["counters"]["symbol_rows"] += 1
    state["counters"]["snapshots_processed"] += 1; state["last_processed_snapshot_utc"] = envelope["captured_at_utc"]

def process_index(state, cfg):
    if not INDEX.exists(): return 0
    count = 0
    with INDEX.open("rb") as f:
        offset = int(state.get("index_offset") or 0); size = INDEX.stat().st_size
        if offset > size: raise RuntimeError("MULTISYMBOL_INDEX_TRUNCATED_FAIL_CLOSED")
        f.seek(offset)
        while True:
            raw = f.readline()
            if not raw: break
            nxt = f.tell()
            if not raw.strip(): state["index_offset"] = nxt; continue
            ref = json.loads(raw.decode("utf-8")); p = Path(ref["path"]); p = p if p.is_absolute() else ROOT / p
            if not p.exists(): break
            env = json.loads(p.read_text(encoding="utf-8"))
            if ref.get("sha256") and env.get("sha256") != ref["sha256"]: raise RuntimeError("MULTISYMBOL_SNAPSHOT_SHA_MISMATCH")
            process_snapshot(state, env, cfg); state["index_offset"] = nxt; count += 1; save(state)
    return count

def main():
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    with LOCK.open("a+") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        cfg = load_cfg(); state = load_state(cfg)
        print(f"MULTISYMBOL_LIVE_STARTED offset={state['index_offset']} mode={state['mode']}", flush=True)
        while True:
            n = process_index(state, cfg)
            if n: print(f"MULTISYMBOL_LIVE_OK new={n} signals={len(state['signals'])}", flush=True)
            time.sleep(LOOP_SECONDS)

if __name__ == "__main__": main()
