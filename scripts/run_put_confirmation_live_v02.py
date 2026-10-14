#!/usr/bin/env python3
from __future__ import annotations

import fcntl
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from options_system.option_costs import daily_regulatory_fees, one_contract_trade
from options_system.prospective_collector import option_latest_quotes
from options_system.put_confirmation_live import (
    VERSION,
    apply_h06_activation,
    expire_machine,
    h06_match,
    snapshot_to_live_row,
)
from options_system.put_research_shadow import DEFAULTS, timestamp
from options_system.session_cache import atomic_text

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / "artifacts/intraday"
INDEX = ROOT / "data/raw/prospective/index.jsonl"
STATE = A / "PUT_CONFIRM_LIVE_STATE_V02.json"
EVENTS = A / "PUT_CONFIRM_LIVE_EVENTS_V02.jsonl"
LOCK = A / ".put_confirm_live_v02.lock"
BASE_CFG = ROOT / "config/put_research_shadow_v01.json"
V02_CFG = ROOT / "config/put_confirmation_shadow_v02.json"
NY = ZoneInfo("America/New_York")
LOOP_SECONDS = 15
FEED = "indicative"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def iso_now() -> str:
    return utcnow().isoformat()


def load_configs():
    base = dict(DEFAULTS)
    base.update(json.loads(BASE_CFG.read_text(encoding="utf-8")))
    v02 = json.loads(V02_CFG.read_text(encoding="utf-8"))
    return base, v02


def fresh_machine():
    return {"status": "IDLE", "arm": None, "locked_until_utc": None}


def initial_state(v02):
    offset = INDEX.stat().st_size if INDEX.exists() else 0
    return {
        "version": VERSION,
        "policy_version": v02["version"],
        "mode": "LIVE_SHADOW_PLUS_ALPACA_PAPER",
        "paper_only": True,
        "scientific_rules_frozen": True,
        "prospective_start_after": v02["prospective_start_after"],
        "live_start_utc": iso_now(),
        "index_offset": offset,
        "session_date": None,
        "machine": fresh_machine(),
        "recent_history": [],
        "signals": [],
        "open_positions": [],
        "live_ledger": [],
        "realized_net_pnl": 0.0,
        "counters": {
            "snapshots_processed": 0,
            "h06_activations": 0,
            "arms": 0,
            "confirmations": 0,
            "paper_entries": 0,
            "paper_closes": 0,
        },
        "last_processed_snapshot_utc": None,
        "updated_at_utc": iso_now(),
    }


def load_state(v02):
    if not STATE.exists():
        state = initial_state(v02)
        save_state(state)
        return state
    try:
        state = json.loads(STATE.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError(f"STATE_CORRUPT_FAIL_CLOSED: {exc}") from exc
    if state.get("policy_version") != v02["version"]:
        raise RuntimeError("POLICY_VERSION_MISMATCH_FAIL_CLOSED")
    return state


def save_state(state):
    state["updated_at_utc"] = iso_now()
    atomic_text(STATE, json.dumps(state, indent=2, ensure_ascii=False) + "\n")


def append_event(event):
    EVENTS.parent.mkdir(parents=True, exist_ok=True)
    payload = {"logged_at_utc": iso_now(), **event}
    with EVENTS.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, sort_keys=True) + "\n")


def in_session_window(now=None):
    now = now or utcnow()
    local = now.astimezone(NY)
    if local.weekday() >= 5:
        return False
    hhmm = local.hour * 60 + local.minute
    return 9 * 60 + 25 <= hhmm <= 16 * 60 + 5


def trim_history(rows, now, minutes=20):
    cutoff = now.timestamp() - minutes * 60
    return [r for r in rows if timestamp(r).timestamp() >= cutoff]


def record_signal(state, signal, row, v02):
    sid = f"PUT_CONFIRM_V02:{row['confirmed_at_utc']}"
    if any(x.get("signal_id") == sid for x in state.get("signals", [])):
        return None

    entry = signal["entry"]
    rec = {
        "signal_id": sid,
        "hypothesis": "PUT_CONFIRM_SHADOW_V02",
        "side": "PUT",
        "decision_date": signal["decision_date"],
        "signal_time": signal["confirmed_at_utc"],
        "armed_at_utc": signal["armed_at_utc"],
        "confirmation_gap_minutes": signal["confirmation_gap_minutes"],
        "contract": entry.get("put_contract"),
        "entry_bid": entry.get("put_entry_bid"),
        "entry_ask": entry.get("put_entry_ask"),
        "entry_bid_size": entry.get("put_entry_bid_size"),
        "entry_ask_size": entry.get("put_entry_ask_size"),
        "quantity": 1,
        "horizon_min": int(v02["execution_evaluation"]["horizon_minutes"]),
        "tp_pct": float(v02["execution_evaluation"]["take_profit_pct"]),
        "sl_pct": -float(v02["execution_evaluation"]["stop_loss_pct"]),
        "scientific_evidence": True,
        "paper_status": "PENDING",
    }
    state.setdefault("signals", []).append(rec)
    state["counters"]["confirmations"] += 1
    append_event({"event": "SIGNAL_CONFIRMED", **rec})

    if state.get("open_positions"):
        blocked = {
            **rec,
            "mode": "LIVE_PAPER",
            "account_kind": "PUT_CONFIRM_V02_LOCAL_SIMULATION",
            "status": "BLOCKED",
            "exit_reason": "PUT_CONFIRM_POSITION_ALREADY_OPEN",
            "net_pnl": None,
        }
        state.setdefault("live_ledger", []).append(blocked)
        rec["paper_status"] = "BLOCKED_CONCURRENT"
        append_event({"event": "PAPER_ENTRY_BLOCKED_CONCURRENT", "signal_id": sid})
        return rec

    ask = rec.get("entry_ask")
    bid = rec.get("entry_bid")
    if ask is None or bid is None or float(ask) <= 0 or float(bid) <= 0:
        rec["paper_status"] = "BLOCKED_INVALID_QUOTE"
        state.setdefault("live_ledger", []).append({
            **rec, "status": "BLOCKED", "exit_reason": "INVALID_ENTRY_QUOTE", "net_pnl": None,
        })
        append_event({"event": "PAPER_ENTRY_BLOCKED_INVALID_QUOTE", "signal_id": sid})
        return rec

    pos = {
        **rec,
        "mode": "LIVE_PAPER",
        "account_kind": "PUT_CONFIRM_V02_LOCAL_SIMULATION",
        "status": "OPEN",
        "entry_time": rec["signal_time"],
        "entry_quote_time": rec["signal_time"],
        "last_bid": bid,
        "last_quote_time": rec["signal_time"],
        "last_mark_time": rec["signal_time"],
        "unrealized_return": None,
        "mfe": 0.0,
        "mae": 0.0,
        "marks": 0,
        "capital_required": float(ask) * 100.0,
    }
    state["open_positions"] = [pos]
    state["counters"]["paper_entries"] += 1
    rec["paper_status"] = "OPEN"
    append_event({"event": "PAPER_ENTRY_OPEN", "signal_id": sid, "contract": rec["contract"], "ask": ask})
    return rec


def process_snapshot(state, envelope, base_cfg, v02):
    row = snapshot_to_live_row(envelope)
    cutoff = str(v02["prospective_start_after"])
    if row["decision_date"] <= cutoff:
        return False

    if state.get("session_date") != row["decision_date"]:
        state["session_date"] = row["decision_date"]
        state["machine"] = fresh_machine()
        state["recent_history"] = []
        append_event({"event": "SESSION_RESET", "decision_date": row["decision_date"]})

    machine = state.setdefault("machine", fresh_machine())
    exp = expire_machine(machine, timestamp(row), v02)
    if exp:
        append_event(exp)

    history = state.setdefault("recent_history", [])
    matched, reason = h06_match(row, history, base_cfg)
    if matched:
        state["counters"]["h06_activations"] += 1
        event, signal = apply_h06_activation(machine, row, v02)
        append_event(event)
        if event["event"] in {"ARMED", "REARMED"}:
            state["counters"]["arms"] += 1
        if signal is not None:
            record_signal(state, signal, signal, v02)
    else:
        state["last_h06_reject_reason"] = reason

    history.append(row)
    state["recent_history"] = trim_history(history, timestamp(row), 20)
    state["last_processed_snapshot_utc"] = row["captured_at_utc"]
    state["counters"]["snapshots_processed"] += 1
    return matched


def process_new_index_rows(state, base_cfg, v02):
    if not INDEX.exists():
        return 0
    processed = 0
    with INDEX.open("rb") as f:
        offset = int(state.get("index_offset") or 0)
        size = INDEX.stat().st_size
        if offset > size:
            raise RuntimeError("INDEX_TRUNCATED_FAIL_CLOSED")
        f.seek(offset)
        while True:
            raw = f.readline()
            if not raw:
                break
            next_offset = f.tell()
            if not raw.strip():
                state["index_offset"] = next_offset
                continue
            ref = json.loads(raw.decode("utf-8"))
            rel = Path(str(ref["path"]))
            path = rel if rel.is_absolute() else ROOT / rel
            if not path.exists():
                break
            envelope = json.loads(path.read_text(encoding="utf-8"))
            if ref.get("sha256") and envelope.get("sha256") != ref.get("sha256"):
                raise RuntimeError(f"SNAPSHOT_INDEX_SHA_MISMATCH: {path.name}")
            process_snapshot(state, envelope, base_cfg, v02)
            state["index_offset"] = next_offset
            processed += 1
            save_state(state)
    return processed


def mark_open_position(state):
    positions = list(state.get("open_positions") or [])
    if not positions:
        return None
    contracts = [p["contract"] for p in positions if p.get("contract")]
    if not contracts:
        return None
    raw = option_latest_quotes(contracts, feed=FEED)
    quotes = raw.get("quotes") or {}
    now = utcnow()
    keep = []
    closed = []

    for pos in positions:
        q = quotes.get(pos["contract"]) or {}
        bid = q.get("bp")
        if bid in (None, "") or float(bid) <= 0:
            keep.append(pos)
            continue
        bid = float(bid)
        entry = float(pos["entry_ask"])
        ret = bid / entry - 1.0
        elapsed = (now - datetime.fromisoformat(pos["entry_time"].replace("Z", "+00:00"))).total_seconds() / 60.0
        pos["last_bid"] = bid
        pos["last_quote_time"] = q.get("t")
        pos["last_mark_time"] = now.isoformat()
        pos["unrealized_return"] = ret
        pos["mfe"] = max(float(pos.get("mfe") or 0.0), ret)
        pos["mae"] = min(float(pos.get("mae") or 0.0), ret)
        pos["marks"] = int(pos.get("marks") or 0) + 1

        reason = None
        if ret >= float(pos["tp_pct"]):
            reason = "TP10"
        elif ret <= float(pos["sl_pct"]):
            reason = "SL10"
        elif elapsed >= float(pos["horizon_min"]):
            reason = "HORIZON"

        if reason is None:
            keep.append(pos)
            continue

        gross = (bid - entry) * 100.0 * int(pos.get("quantity") or 1)
        model = one_contract_trade(entry, ret)
        fee_one = float(daily_regulatory_fees([model])["total"]) if model else 0.0
        fees = fee_one * int(pos.get("quantity") or 1)
        net = gross - fees
        pos.update({
            "status": "CLOSED",
            "exit_time": now.isoformat(),
            "exit_bid": bid,
            "exit_reason": reason,
            "gross_pnl": gross,
            "fees": fees,
            "net_pnl": net,
        })
        closed.append(pos)
        state["realized_net_pnl"] = float(state.get("realized_net_pnl") or 0.0) + net
        state["counters"]["paper_closes"] += 1
        append_event({"event": "PAPER_POSITION_CLOSED", "signal_id": pos["signal_id"], "reason": reason, "net_pnl": net})

    state["open_positions"] = keep
    state.setdefault("live_ledger", []).extend(closed)
    return closed


def run_cycle(state, base_cfg, v02):
    marked = mark_open_position(state) if state.get("open_positions") else None
    new_rows = process_new_index_rows(state, base_cfg, v02)
    if marked or new_rows:
        save_state(state)
    return new_rows, len(marked or [])


def main():
    base_cfg, v02 = load_configs()
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    lock_handle = LOCK.open("w", encoding="utf-8")
    try:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise SystemExit("PUT_CONFIRM_LIVE_ALREADY_RUNNING")
    lock_handle.write(f"pid={os.getpid()} started={iso_now()}\n")
    lock_handle.flush()

    state = load_state(v02)
    print(
        "PUT_CONFIRM_LIVE_STARTED",
        f"policy={v02['version']}",
        f"interval={LOOP_SECONDS}s",
        f"start={state['live_start_utc']}",
        flush=True,
    )

    while True:
        try:
            if in_session_window():
                rows, closes = run_cycle(state, base_cfg, v02)
                if rows or closes:
                    print(
                        "PUT_CONFIRM_LIVE_OK",
                        f"new_snapshots={rows}",
                        f"machine={state['machine']['status']}",
                        f"open={len(state.get('open_positions') or [])}",
                        f"signals={len(state.get('signals') or [])}",
                        f"closes={closes}",
                        flush=True,
                    )
                time.sleep(LOOP_SECONDS)
            else:
                time.sleep(60)
        except Exception as exc:
            print(f"PUT_CONFIRM_LIVE_ERROR {type(exc).__name__}: {exc}", flush=True)
            time.sleep(LOOP_SECONDS)


if __name__ == "__main__":
    main()
