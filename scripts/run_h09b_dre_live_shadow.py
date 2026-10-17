#!/usr/bin/env python3
from __future__ import annotations

import fcntl
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from options_system.h09b_dre import SOURCE_CANDIDATE, VERSION, parse_time, quote_for_contract, route_signal, touch10_triggered
from options_system.session_cache import atomic_text

ROOT = Path(__file__).resolve().parents[1]
CFG = ROOT / "config/h09b_dre_v01.json"
H09_EVENTS = ROOT / "artifacts/intraday/H09_PUT_FLOW_LIVE_EVENTS_V01.jsonl"
INDEX = ROOT / "data/raw/prospective/index.jsonl"
STATE = ROOT / "artifacts/intraday/H09B_DRE_LIVE_STATE_V01.json"
EVENTS = ROOT / "artifacts/intraday/H09B_DRE_LIVE_EVENTS_V01.jsonl"
LOCK = ROOT / "artifacts/intraday/.h09b_dre_live.lock"
LOOP_SECONDS = 10


def now_iso(): return datetime.now(timezone.utc).isoformat()
def load_cfg(): return json.loads(CFG.read_text(encoding="utf-8"))


def initial_state(cfg):
    return {
        "version": VERSION, "policy_version": cfg["version"], "mode": "LIVE_SHADOW_NO_ORDERS",
        "paper_only": True, "auto_apply": False, "broker_orders_enabled": False,
        "prospective_start_after": cfg["prospective_start_after"], "live_start_utc": now_iso(),
        "h09_events_offset": H09_EVENTS.stat().st_size if H09_EVENTS.exists() else 0,
        "index_offset": INDEX.stat().st_size if INDEX.exists() else 0,
        "armed": {}, "recent_decisions": [], "recent_entries": [], "recent_expirations": [],
        "counters": {"signals_seen": 0, "buy_now": 0, "armed": 0, "blocked": 0, "arm_entries": 0, "expired": 0},
        "updated_at_utc": now_iso(),
    }


def save(state):
    state["updated_at_utc"] = now_iso()
    atomic_text(STATE, json.dumps(state, indent=2) + "\n")


def log_event(payload):
    EVENTS.parent.mkdir(parents=True, exist_ok=True)
    with EVENTS.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"logged_at_utc": now_iso(), **payload}, sort_keys=True) + "\n")


def load_state(cfg):
    if not STATE.exists():
        state = initial_state(cfg); save(state); return state
    state = json.loads(STATE.read_text(encoding="utf-8"))
    if state.get("policy_version") != cfg["version"]:
        raise RuntimeError("H09B_DRE_POLICY_VERSION_MISMATCH_FAIL_CLOSED")
    return state


def add_recent(state, key, row, limit=100):
    state[key].append(row)
    state[key] = state[key][-limit:]


def process_signal(state, row, cfg):
    if row.get("event") != "H09_SIGNAL" or row.get("candidate_id") != SOURCE_CANDIDATE:
        return
    day = str(row.get("decision_date") or "")
    if not day or day <= cfg["prospective_start_after"]:
        return
    state["counters"]["signals_seen"] += 1
    route = route_signal(row.get("entry_bid"), row.get("entry_ask"), cfg)
    decision = {
        "event": "DRE_DECISION", "signal_id": row.get("signal_id"), "decision_date": day,
        "signal_time": row.get("signal_time"), "contract": row.get("contract"), "side": "PUT",
        "entry_bid": row.get("entry_bid"), "entry_ask": row.get("entry_ask"),
        "spread_pct": route.get("spread_pct"), "decision": route["decision"], "reason": route["reason"],
        "broker_order": False,
    }
    add_recent(state, "recent_decisions", decision); log_event(decision)
    if route["decision"] == "BUY_NOW":
        state["counters"]["buy_now"] += 1
        entry = {**decision, "event": "DRE_SHADOW_ENTRY", "entry_policy": "BUY_NOW", "shadow_entry_time": row.get("signal_time"), "shadow_entry_bid": row.get("entry_bid"), "shadow_entry_ask": row.get("entry_ask")}
        add_recent(state, "recent_entries", entry); log_event(entry)
    elif route["decision"] == "ARM_TOUCH10":
        state["counters"]["armed"] += 1
        state["armed"][row["signal_id"]] = {
            "signal_id": row["signal_id"], "decision_date": day, "signal_time": row["signal_time"],
            "contract": row.get("contract"), "initial_bid": row.get("entry_bid"), "initial_ask": row.get("entry_ask"),
            "spread_pct": route.get("spread_pct"), "status": "ARMED", "lowest_mark": 0.0,
        }
    else:
        state["counters"]["blocked"] += 1


def process_h09_events(state, cfg):
    if not H09_EVENTS.exists(): return 0
    count = 0
    with H09_EVENTS.open("rb") as f:
        offset = int(state.get("h09_events_offset") or 0); size = H09_EVENTS.stat().st_size
        if offset > size: raise RuntimeError("H09B_DRE_H09_EVENTS_TRUNCATED_FAIL_CLOSED")
        f.seek(offset)
        while True:
            raw = f.readline()
            if not raw: break
            nxt = f.tell(); state["h09_events_offset"] = nxt
            if not raw.strip(): continue
            process_signal(state, json.loads(raw.decode("utf-8")), cfg); count += 1
    return count


def process_snapshot_for_arms(state, envelope, cfg):
    if not state["armed"]: return
    captured = parse_time(envelope["captured_at_utc"])
    remove = []
    for signal_id, arm in list(state["armed"].items()):
        elapsed = (captured - parse_time(arm["signal_time"])).total_seconds() / 60.0
        if elapsed < 0: continue
        if elapsed > float(cfg["horizon_minutes"]):
            exp = {"event": "DRE_ARM_EXPIRED", **arm, "expired_at": envelope["captured_at_utc"], "elapsed_minutes": elapsed, "broker_order": False}
            add_recent(state, "recent_expirations", exp); log_event(exp); state["counters"]["expired"] += 1; remove.append(signal_id); continue
        quote = quote_for_contract(envelope, arm["contract"])
        if not quote: continue
        hit, mark = touch10_triggered(arm["initial_ask"], quote["bid"], cfg)
        if mark is not None: arm["lowest_mark"] = min(float(arm.get("lowest_mark") or 0), mark)
        if not hit: continue
        entry = {
            "event": "DRE_SHADOW_ENTRY", "signal_id": signal_id, "decision_date": arm["decision_date"], "signal_time": arm["signal_time"],
            "contract": arm["contract"], "side": "PUT", "entry_policy": "ARM_TOUCH10", "original_ask": arm["initial_ask"],
            "trigger_mark_return": mark, "shadow_entry_time": envelope["captured_at_utc"], "shadow_entry_bid": quote["bid"], "shadow_entry_ask": quote["ask"],
            "spread_pct_at_signal": arm["spread_pct"], "broker_order": False,
        }
        add_recent(state, "recent_entries", entry); log_event(entry); state["counters"]["arm_entries"] += 1; remove.append(signal_id)
    for signal_id in remove: state["armed"].pop(signal_id, None)


def process_index(state, cfg):
    if not INDEX.exists(): return 0
    count = 0
    with INDEX.open("rb") as f:
        offset = int(state.get("index_offset") or 0); size = INDEX.stat().st_size
        if offset > size: raise RuntimeError("H09B_DRE_INDEX_TRUNCATED_FAIL_CLOSED")
        f.seek(offset)
        while True:
            raw = f.readline()
            if not raw: break
            nxt = f.tell()
            if not raw.strip(): state["index_offset"] = nxt; continue
            ref = json.loads(raw.decode("utf-8")); p = Path(ref["path"]); p = p if p.is_absolute() else ROOT / p
            if not p.exists(): break
            envelope = json.loads(p.read_text(encoding="utf-8"))
            if ref.get("sha256") and envelope.get("sha256") != ref["sha256"]: raise RuntimeError("H09B_DRE_SNAPSHOT_SHA_MISMATCH")
            process_snapshot_for_arms(state, envelope, cfg); state["index_offset"] = nxt; count += 1
    return count


def run_once(state, cfg):
    a = process_h09_events(state, cfg); b = process_index(state, cfg); save(state); return a, b


def main():
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    with LOCK.open("a+") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        cfg = load_cfg(); state = load_state(cfg)
        print(f"H09B_DRE_LIVE_STARTED policy={cfg['version']} h09_offset={state['h09_events_offset']} index_offset={state['index_offset']} mode={state['mode']}", flush=True)
        if "--once" in sys.argv:
            print("H09B_DRE_ONCE", run_once(state, cfg), flush=True); return
        while True:
            a, b = run_once(state, cfg)
            if a or b: print(f"H09B_DRE_LIVE_OK h09_events={a} snapshots={b} armed={len(state['armed'])} entries={len(state['recent_entries'])}", flush=True)
            time.sleep(LOOP_SECONDS)


if __name__ == "__main__": main()
