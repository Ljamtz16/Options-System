#!/usr/bin/env python3
from __future__ import annotations

import json
import time
from datetime import datetime, time as dtime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from options_system.entry_controls import entry_block, update_session_risk
from options_system.executable_contracts import select_signal
from options_system.frozen_live_engine import (
    H03_ID,
    VERSION,
    add_previous_deltas,
    compact_feature_memory,
    episode_activation,
    live_hypothesis_active,
    open_reference_stable,
    signal_from_row,
    stamp,
)
from options_system.intraday_session import snapshot_close
from options_system.option_costs import daily_regulatory_fees, one_contract_trade
from options_system.paper_epochs import acquire_state_lock
from options_system.prospective_collector import option_latest_quotes
from options_system.prospective_dataset import snapshot_to_row
from options_system.prospective_execution_gate import evaluate_execution
from options_system.prospective_hypothesis_tracker import hypothesis_active
from options_system.session_cache import atomic_text

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / "artifacts/intraday"
INDEX = ROOT / "data/raw/prospective/index.jsonl"
ACCOUNT_STATE = A / "PAPER_TRADING_LIVE_STATE_V01.json"
ENGINE_STATE = A / "FROZEN_HYPOTHESES_LIVE_ENGINE_V01.json"
EVENTS = A / "FROZEN_HYPOTHESES_LIVE_EVENTS_V01.jsonl"
FROZEN = A / "FROZEN_HYPOTHESES_V02.json"
RISK = A / "PROSPECTIVE_RISK_GATE_V01.json"
CONTROL = A / "PAPER_TRADING_CONTROL_V01.json"
NY = ZoneInfo("America/New_York")
LOOP_SECONDS = 15
OUTSIDE_WINDOW_SLEEP = 60
TP = 0.10
SL = -0.10
MAX_CONTRACTS = 1


def now_utc():
    return datetime.now(timezone.utc)


def iso_now():
    return now_utc().isoformat()


def append_event(event):
    EVENTS.parent.mkdir(parents=True, exist_ok=True)
    with EVENTS.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"logged_at_utc": iso_now(), **event}, sort_keys=True) + "\n")


def save_json(path, obj):
    atomic_text(path, json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


def in_session_window(now=None):
    local = (now or now_utc()).astimezone(NY)
    return local.weekday() < 5 and dtime(9, 25) <= local.time().replace(tzinfo=None) <= dtime(16, 5)


def initial_engine_state():
    return {
        "version": VERSION,
        "mode": "LIVE_FROZEN_HYPOTHESES",
        "live_start_utc": iso_now(),
        "index_offset": INDEX.stat().st_size if INDEX.exists() else 0,
        "previous_feature_memory": None,
        "episodes": {},
        "counters": {
            "snapshots_processed": 0,
            "activations": 0,
            "new_episodes": 0,
            "entries_opened": 0,
            "entries_blocked": 0,
            "positions_closed": 0,
            "h03_data_quality_blocks": 0,
        },
        "last_processed_snapshot_utc": None,
        "last_h03_open_guard": None,
        "updated_at_utc": iso_now(),
    }


def load_engine():
    if not ENGINE_STATE.exists():
        state = initial_engine_state()
        save_json(ENGINE_STATE, state)
        return state
    state = json.loads(ENGINE_STATE.read_text(encoding="utf-8"))
    if state.get("version") != VERSION:
        raise RuntimeError("FROZEN_LIVE_ENGINE_VERSION_MISMATCH_FAIL_CLOSED")
    return state


def load_runtime_policy():
    risk = json.loads(RISK.read_text(encoding="utf-8"))
    control = json.loads(CONTROL.read_text(encoding="utf-8")) if CONTROL.exists() else {"risk_fraction": 0.20}
    fraction = float(control.get("risk_fraction", 0.20))
    paper_gate = dict(risk)
    paper_gate["allowed_max_fraction"] = fraction
    paper_gate["status"] = "ACTIVE" if fraction > 0 else "BLOCKED"
    return fraction, paper_gate, dict(control.get("entry_controls") or {})


def block_record(account, signal, reason, cash, **extra):
    rec = {
        **signal,
        **extra,
        "mode": "LIVE_PAPER",
        "account_kind": "LOCAL_SIMULATION",
        "status": "BLOCKED",
        "exit_reason": reason,
        "gross_pnl": 0.0,
        "fees": 0.0,
        "net_pnl": 0.0,
        "cash_after": cash,
    }
    account.setdefault("live_ledger", []).append(rec)
    append_event({"event": "ENTRY_BLOCKED", "signal_id": signal["signal_id"], "reason": reason})


def open_signal(account, envelope, signal, paper_fraction, paper_gate, entry_policy):
    cash = float(account["cash"])
    ledger = account.setdefault("live_ledger", [])
    open_positions = {x["signal_id"]: x for x in account.get("open_positions") or []}
    session_risk = dict(account.get("session_risk") or {})
    now = stamp(signal["signal_time"])
    update_session_risk(session_risk, now, cash, open_positions, ledger)

    block = entry_block(signal, now, open_positions, ledger, session_risk, entry_policy)
    if block:
        block_record(account, signal, block, cash)
        return False

    selected = select_signal(envelope, signal, cash, paper_fraction)
    episode = {k: selected.get(k) for k in ("contract", "entry_ask", "entry_bid", "entry_ask_size", "entry_bid_size")}
    gate = evaluate_execution(episode, paper_gate, cash=cash)
    record = {
        **selected,
        "mode": "LIVE_PAPER",
        "account_kind": "LOCAL_SIMULATION",
        "execution_gate": gate,
        "cash_before": cash,
    }
    if gate["status"] != "PASS":
        block_record(account, selected, "EXECUTION_GATE", cash, execution_gate=gate)
        return False

    qty = min(MAX_CONTRACTS, int(gate.get("max_contracts_by_risk_budget") or 0))
    if qty < 1:
        block_record(account, selected, "NO_ALLOWED_QUANTITY", cash, execution_gate=gate)
        return False

    ask = float(selected["entry_ask"])
    capital = ask * 100.0 * qty
    if capital > cash:
        block_record(account, selected, "INSUFFICIENT_CASH", cash, execution_gate=gate)
        return False

    account["cash"] = cash - capital
    position = {
        **record,
        "status": "OPEN",
        "session_close_at_utc": snapshot_close(envelope),
        "quantity": qty,
        "capital_required": capital,
        "entry_time": signal["signal_time"],
        "entry_quote_time": selected.get("entry_quote_time"),
        "last_bid": selected.get("entry_bid"),
        "last_quote_time": selected.get("entry_quote_time"),
        "last_mark_time": signal["signal_time"],
        "unrealized_return": None,
        "mfe": 0.0,
        "mae": 0.0,
        "marks": 0,
        "cash_after_entry": account["cash"],
        "live_engine_version": VERSION,
    }
    account.setdefault("open_positions", []).append(position)
    append_event({"event": "ENTRY_OPEN", "signal_id": signal["signal_id"], "contract": position["contract"], "ask": ask})
    return True


def process_snapshot(account, engine, path, frozen, paper_fraction, paper_gate, entry_policy):
    envelope = json.loads(path.read_text(encoding="utf-8"))
    row = snapshot_to_row(path)
    previous = engine.get("previous_feature_memory")
    row = add_previous_deltas(row, previous)
    current_memory = compact_feature_memory(row, envelope)
    stable, guard_reason = open_reference_stable(previous, current_memory)
    engine["last_h03_open_guard"] = {"stable": stable, "reason": guard_reason, "at_utc": row["captured_at_utc"]}

    seen = set(account.get("seen_signal_ids") or [])
    for hypothesis in frozen["hypotheses"]:
        raw_active = hypothesis_active(hypothesis, row)
        active, active_reason = live_hypothesis_active(hypothesis, row, h03_open_stable=stable)
        if hypothesis["id"] == H03_ID and raw_active and not stable:
            engine["counters"]["h03_data_quality_blocks"] += 1
            append_event({"event": "H03_DATA_QUALITY_BLOCK", "at_utc": row["captured_at_utc"], "reason": guard_reason})
        if not active:
            continue

        engine["counters"]["activations"] += 1
        ep, sid = episode_activation(engine.setdefault("episodes", {}).get(hypothesis["id"]), hypothesis, row)
        engine["episodes"][hypothesis["id"]] = ep
        if sid is None or sid in seen:
            continue

        signal = signal_from_row(hypothesis, row, sid)
        seen.add(sid)
        account["seen_signal_ids"] = sorted(seen)
        engine["counters"]["new_episodes"] += 1
        append_event({"event": "SIGNAL", "signal_id": sid, "hypothesis": hypothesis["id"], "signal_time": signal["signal_time"]})
        if open_signal(account, envelope, signal, paper_fraction, paper_gate, entry_policy):
            engine["counters"]["entries_opened"] += 1
        else:
            engine["counters"]["entries_blocked"] += 1

    engine["previous_feature_memory"] = current_memory
    engine["last_processed_snapshot_utc"] = row["captured_at_utc"]
    engine["counters"]["snapshots_processed"] += 1
    account["last_processed_snapshot_utc"] = row["captured_at_utc"]


def process_new_snapshots(account, engine, frozen, paper_fraction, paper_gate, entry_policy):
    if not INDEX.exists():
        return 0
    processed = 0
    with INDEX.open("rb") as f:
        offset = int(engine.get("index_offset") or 0)
        size = INDEX.stat().st_size
        if offset > size:
            raise RuntimeError("PROSPECTIVE_INDEX_TRUNCATED_FAIL_CLOSED")
        f.seek(offset)
        while True:
            raw = f.readline()
            if not raw:
                break
            next_offset = f.tell()
            if not raw.strip():
                engine["index_offset"] = next_offset
                continue
            ref = json.loads(raw.decode("utf-8"))
            path = Path(str(ref["path"]))
            if not path.is_absolute():
                path = ROOT / path
            if not path.exists():
                break
            process_snapshot(account, engine, path, frozen, paper_fraction, paper_gate, entry_policy)
            engine["index_offset"] = next_offset
            processed += 1
    return processed


def mark_positions(account, engine):
    positions = list(account.get("open_positions") or [])
    if not positions:
        return 0
    contracts = [p.get("contract") for p in positions if p.get("contract")]
    if not contracts:
        return 0
    raw = option_latest_quotes(contracts, feed="indicative")
    quotes = raw.get("quotes") or {}
    now = now_utc()
    keep, closed = [], []

    for pos in positions:
        q = quotes.get(pos.get("contract")) or {}
        bid = q.get("bp")
        if bid in (None, "") or float(bid) <= 0:
            keep.append(pos)
            continue
        bid = float(bid)
        entry = float(pos["entry_ask"])
        ret = bid / entry - 1.0
        elapsed = (now - stamp(pos["entry_time"])).total_seconds() / 60.0
        pos["last_bid"] = bid
        pos["last_quote_time"] = q.get("t")
        pos["last_mark_time"] = now.isoformat()
        pos["unrealized_return"] = ret
        pos["mfe"] = max(float(pos.get("mfe") or 0.0), ret)
        pos["mae"] = min(float(pos.get("mae") or 0.0), ret)
        pos["marks"] = int(pos.get("marks") or 0) + 1

        reason = None
        if ret >= TP:
            reason = "TP10"
        elif ret <= SL:
            reason = "SL10"
        elif elapsed >= float(pos["horizon_min"]):
            reason = "HORIZON"
        close_at = pos.get("session_close_at_utc")
        if reason is None and close_at and now >= stamp(close_at):
            reason = "SESSION_CLOSE"
        if reason is None:
            keep.append(pos)
            continue

        qty = int(pos.get("quantity") or 1)
        model = one_contract_trade(entry, ret)
        fee_one = float(daily_regulatory_fees([model])["total"]) if model else 0.0
        fees = fee_one * qty
        gross = (bid - entry) * 100.0 * qty
        net = gross - fees
        account["cash"] = float(account["cash"]) + bid * 100.0 * qty - fees
        account["realized_net_pnl"] = float(account.get("realized_net_pnl") or 0.0) + net
        pos.update({"status": "CLOSED", "exit_time": now.isoformat(), "exit_bid": bid, "exit_reason": reason,
                    "gross_pnl": gross, "fees": fees, "net_pnl": net, "cash_after": account["cash"]})
        account.setdefault("live_ledger", []).append(dict(pos))
        closed.append(pos)
        append_event({"event": "POSITION_CLOSED", "signal_id": pos["signal_id"], "reason": reason, "net_pnl": net})

    account["open_positions"] = keep
    engine["counters"]["positions_closed"] += len(closed)
    return len(closed)


def finalize_account(account, entry_policy, paper_fraction, scientific_fraction):
    open_positions = {x["signal_id"]: x for x in account.get("open_positions") or []}
    ledger = account.get("live_ledger") or []
    cash = float(account["cash"])
    session_risk = dict(account.get("session_risk") or {})
    update_session_risk(session_risk, now_utc(), cash, open_positions, ledger)
    reserved = sum(float(x.get("capital_required") or 0.0) for x in open_positions.values())
    unrealized = sum((float(x.get("last_bid") or x["entry_ask"]) - float(x["entry_ask"])) * 100.0 * int(x.get("quantity") or 1)
                     for x in open_positions.values())
    equity = cash + reserved + unrealized
    account.update({
        "mode": "LIVE_PAPER",
        "account_kind": "LOCAL_SIMULATION",
        "entry_controls": entry_policy,
        "session_risk": session_risk,
        "live_engine_version": VERSION,
        "paper_risk_fraction": paper_fraction,
        "scientific_risk_fraction": scientific_fraction,
        "reserved_capital": reserved,
        "unrealized_pnl": unrealized,
        "equity": equity,
        "net_account_pnl": equity - float(account["initial_cash"]),
        "closed_live_trades": sum(x.get("status") == "CLOSED" for x in ledger),
        "blocked_live_signals": sum(x.get("status") == "BLOCKED" for x in ledger),
        "updated_at_utc": iso_now(),
    })


def run_iteration(frozen, scientific_fraction):
    engine = load_engine()
    paper_fraction, paper_gate, entry_policy = load_runtime_policy()
    with acquire_state_lock(ACCOUNT_STATE):
        if not ACCOUNT_STATE.exists():
            raise RuntimeError("PAPER_TRADING_LIVE_STATE_REQUIRED")
        account = json.loads(ACCOUNT_STATE.read_text(encoding="utf-8"))
        new_count = process_new_snapshots(account, engine, frozen, paper_fraction, paper_gate, entry_policy)
        close_count = mark_positions(account, engine)
        finalize_account(account, entry_policy, paper_fraction, scientific_fraction)
        save_json(ACCOUNT_STATE, account)
        engine["updated_at_utc"] = iso_now()
        save_json(ENGINE_STATE, engine)
    return new_count, close_count, engine, account


def main():
    frozen = json.loads(FROZEN.read_text(encoding="utf-8"))
    risk = json.loads(RISK.read_text(encoding="utf-8"))
    scientific_fraction = float(risk.get("allowed_max_fraction") or 0.0)
    load_engine()
    print(f"FROZEN_HYPOTHESES_LIVE_STARTED version={VERSION} interval={LOOP_SECONDS}s", flush=True)
    while True:
        try:
            if in_session_window():
                new_count, close_count, engine, account = run_iteration(frozen, scientific_fraction)
                if new_count or close_count:
                    print("FROZEN_LIVE_OK", f"new_snapshots={new_count}", f"closes={close_count}",
                          f"open={len(account.get('open_positions') or [])}",
                          f"net={float(account.get('net_account_pnl') or 0):.2f}", flush=True)
                time.sleep(LOOP_SECONDS)
            else:
                time.sleep(OUTSIDE_WINDOW_SLEEP)
        except Exception as exc:
            append_event({"event": "ENGINE_ERROR", "error": repr(exc)})
            print(f"FROZEN_LIVE_ERROR {type(exc).__name__}: {exc}", flush=True)
            time.sleep(LOOP_SECONDS)


if __name__ == "__main__":
    main()
