#!/usr/bin/env python3
from __future__ import annotations

import fcntl
import json
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from options_system.meta_decision_layer import market_regime
from options_system.meta_decision_live import (
    context_from_envelope,
    context_ready_for_day,
    episode_metrics,
    h01_decision,
    h09_decision,
    health_flags_from_closed,
    multi_decision,
)
from options_system.session_cache import atomic_text

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts/intraday"
CFG = ROOT / "config/meta_decision_layer_v01.json"
PAPER = ART / "PAPER_TRADING_LIVE_STATE_V01.json"
H09 = ART / "H09_PUT_FLOW_LIVE_STATE_V01.json"
MULTI = ART / "MULTISYMBOL_LIVE_STATE_V01.json"
SPY_INDEX = ROOT / "data/raw/prospective/index.jsonl"
STATE = ART / "META_DECISION_LIVE_STATE_V01.json"
EVENTS = ART / "META_DECISION_LIVE_EVENTS_V01.jsonl"
LOCK = ART / ".meta_decision_live_v01.lock"
LOOP_SECONDS = 5
MAX_RECENT_DECISIONS = 500


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def load_cfg() -> dict[str, Any]:
    return load_json(CFG, {})


def source_lengths() -> dict[str, int]:
    paper = load_json(PAPER, {})
    h09 = load_json(H09, {})
    multi = load_json(MULTI, {})
    return {
        "h01_ledger": len(paper.get("live_ledger") or []),
        "h09_signals": len(h09.get("signals") or []),
        "multi_signals": len(multi.get("signals") or []),
    }


def latest_context_from_index() -> dict[str, Any] | None:
    if not SPY_INDEX.exists() or SPY_INDEX.stat().st_size == 0:
        return None
    with SPY_INDEX.open("rb") as f:
        pos = SPY_INDEX.stat().st_size - 1
        buf = bytearray()
        while pos >= 0:
            f.seek(pos)
            ch = f.read(1)
            if ch == b"\n" and buf:
                break
            if ch != b"\n":
                buf.extend(ch)
            pos -= 1
    if not buf:
        return None
    raw = bytes(reversed(buf)).decode("utf-8")
    ref = json.loads(raw)
    p = Path(ref["path"])
    p = p if p.is_absolute() else ROOT / p
    if not p.exists():
        return None
    env = json.loads(p.read_text(encoding="utf-8"))
    if ref.get("sha256") and env.get("sha256") != ref["sha256"]:
        raise RuntimeError("META_LIVE_CONTEXT_SHA_MISMATCH")
    return context_from_envelope(env)


def initial_state(cfg: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": "META_DECISION_LIVE_SHADOW_V01",
        "policy_version": cfg.get("version"),
        "mode": "LIVE_SHADOW_NO_ORDERS",
        "auto_apply": False,
        "broker_orders_enabled": False,
        "live_start_utc": now_iso(),
        "prospective_start_after": cfg.get("prospective_start_after"),
        "source_cursors": source_lengths(),
        "latest_context": latest_context_from_index(),
        "recent_decisions": [],
        "counters": {"processed": 0, "accept": 0, "wait": 0, "block": 0, "by_source": {}},
        "updated_at_utc": now_iso(),
    }


def save(state: dict[str, Any]) -> None:
    state["updated_at_utc"] = now_iso()
    atomic_text(STATE, json.dumps(state, indent=2) + "\n")


def log_event(payload: dict[str, Any]) -> None:
    EVENTS.parent.mkdir(parents=True, exist_ok=True)
    with EVENTS.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"logged_at_utc": now_iso(), **payload}, sort_keys=True) + "\n")


def load_state(cfg: dict[str, Any]) -> dict[str, Any]:
    if not STATE.exists():
        state = initial_state(cfg)
        save(state)
        log_event({"event": "META_LIVE_BASELINE", "source_cursors": state["source_cursors"]})
        return state
    state = load_json(STATE, {})
    if state.get("policy_version") != cfg.get("version"):
        raise RuntimeError("META_LIVE_POLICY_VERSION_MISMATCH_FAIL_CLOSED")
    return state


def append_decision(state: dict[str, Any], row: dict[str, Any]) -> None:
    state["recent_decisions"].append(row)
    state["recent_decisions"] = state["recent_decisions"][-MAX_RECENT_DECISIONS:]
    decision = row["decision"].lower()
    state["counters"]["processed"] += 1
    state["counters"][decision] += 1
    src = row["source"]
    bucket = state["counters"]["by_source"].setdefault(src, {"processed": 0, "accept": 0, "wait": 0, "block": 0})
    bucket["processed"] += 1
    bucket[decision] += 1
    log_event({"event": "META_DECISION", **row})


def current_context(state: dict[str, Any]) -> dict[str, Any]:
    fresh = latest_context_from_index()
    if fresh:
        state["latest_context"] = fresh
    return state.get("latest_context") or {}


def process_h01(state: dict[str, Any], cfg: dict[str, Any], paper: dict[str, Any], context: dict[str, Any]) -> int:
    ledger = paper.get("live_ledger") or []
    cursor = int(state["source_cursors"].get("h01_ledger", 0))
    if len(ledger) < cursor:
        raise RuntimeError("META_LIVE_H01_LEDGER_TRUNCATED_FAIL_CLOSED")
    history = state.get("recent_decisions") or []
    count = 0
    base_cursor = cursor
    for rel_idx, trade in enumerate(ledger[base_cursor:]):
        absolute_idx = base_cursor + rel_idx
        if trade.get("hypothesis") != "CALL_FLOW_REVERSAL_V01":
            continue
        stamp = str(trade.get("signal_time") or trade.get("entry_time") or "")
        if not stamp:
            continue
        prior_closed = [r for r in ledger[:absolute_idx] if r.get("hypothesis") == "CALL_FLOW_REVERSAL_V01" and r.get("status") == "CLOSED" and str(r.get("exit_time") or "") <= stamp]
        flags = health_flags_from_closed(prior_closed, context.get("vix_change_pct"))
        epi = episode_metrics(history, "H01", "SPY", "CALL", stamp, cfg["episode_window_minutes"], cfg["flicker_window_minutes"])
        executable = bool((trade.get("execution_gate") or {}).get("executable", trade.get("contract") and trade.get("entry_ask")))
        ready = context_ready_for_day(context, str(trade.get("decision_date") or ""))
        regime = str(context.get("market_regime") or "UNKNOWN") if ready else "UNKNOWN"
        decision, block, wait = h01_decision(executable, flags, regime, epi["is_episode_repeat"], ready)
        row = {
            "meta_decision_id": f"META:H01:{trade.get('signal_id')}", "source": "H01", "source_signal_ids": [trade.get("signal_id")],
            "strategy": trade.get("hypothesis"), "symbol": "SPY", "side": "CALL", "day": trade.get("decision_date"), "time": stamp,
            "contract": trade.get("contract"), "entry_ask": trade.get("entry_ask"), "executable": executable,
            "market_regime": regime, "vix_change_pct": context.get("vix_change_pct"), "health_flags": flags,
            "decision": decision, "block_reasons": block, "wait_reasons": wait, "broker_order": False, "auto_apply": False, **epi,
        }
        append_decision(state, row); history = state["recent_decisions"]; count += 1
    state["source_cursors"]["h01_ledger"] = len(ledger)
    return count


def process_h09(state: dict[str, Any], cfg: dict[str, Any], h09: dict[str, Any]) -> int:
    signals = h09.get("signals") or []
    cursor = int(state["source_cursors"].get("h09_signals", 0))
    if len(signals) < cursor:
        raise RuntimeError("META_LIVE_H09_TRUNCATED_FAIL_CLOSED")
    new = signals[cursor:]
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for sig in new:
        grouped[str(sig.get("signal_time"))].append(sig)
    history = state.get("recent_decisions") or []
    count = 0
    for stamp, variants in sorted(grouped.items()):
        ids = {str(v.get("candidate_id")) for v in variants}
        is_b = "H09B_PUT_FLOW_MIRROR_RISKOFF_V01" in ids
        raw = next((v for v in variants if v.get("candidate_id") == "H09B_PUT_FLOW_MIRROR_RISKOFF_V01"), variants[0])
        regime = market_regime(raw.get("spy_from_open"), raw.get("qqq_from_open"), raw.get("iwm_from_open"))
        decision, block, wait, spread = h09_decision(is_b, raw.get("contract"), raw.get("entry_ask"), raw.get("entry_bid"), regime,
                                                      float(cfg["h09"]["max_contract_price"]), float(cfg["h09"]["max_spread_pct"]))
        epi = episode_metrics(history, "H09", "SPY", "PUT", stamp, cfg["episode_window_minutes"], cfg["flicker_window_minutes"])
        row = {
            "meta_decision_id": f"META:H09:{stamp}", "source": "H09", "source_signal_ids": [v.get("signal_id") for v in variants],
            "strategy": "H09B_PUT_FLOW_MIRROR_RISKOFF_V01" if is_b else "H09A_PUT_FLOW_MIRROR_V01", "candidate_ids": sorted(ids),
            "symbol": "SPY", "side": "PUT", "day": raw.get("decision_date"), "time": stamp, "contract": raw.get("contract"),
            "entry_ask": raw.get("entry_ask"), "spread_pct": spread, "market_regime": regime,
            "decision": decision, "block_reasons": block, "wait_reasons": wait, "broker_order": False, "auto_apply": False, **epi,
        }
        append_decision(state, row); history = state["recent_decisions"]; count += 1
    state["source_cursors"]["h09_signals"] = len(signals)
    return count


def process_multi(state: dict[str, Any], cfg: dict[str, Any], multi: dict[str, Any]) -> int:
    signals = multi.get("signals") or []
    cursor = int(state["source_cursors"].get("multi_signals", 0))
    if len(signals) < cursor:
        raise RuntimeError("META_LIVE_MULTI_TRUNCATED_FAIL_CLOSED")
    new = signals[cursor:]
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for sig in new:
        grouped[(str(sig.get("signal_time")), str(sig.get("symbol")), str(sig.get("side") or "").upper())].append(sig)
    history = list(state.get("recent_decisions") or [])
    batch_rows: list[dict[str, Any]] = []
    for (stamp, symbol, side), variants in sorted(grouped.items()):
        raw = variants[0]
        regime = market_regime(raw.get("market_spy_from_first"), raw.get("market_qqq_from_first"), raw.get("market_iwm_from_first"))
        ids = sorted({str(v.get("candidate_id")) for v in variants})
        decision, block, wait, spread = multi_decision(side, raw.get("contract"), raw.get("entry_ask"), raw.get("entry_bid"), regime, len(ids),
                                                       float(cfg["multi"]["max_contract_price"]), float(cfg["multi"]["max_market_spread_pct"]),
                                                       int(cfg["multi"]["redundant_support_count_ge"]))
        epi = episode_metrics(history, "MULTI", symbol, side, stamp, cfg["episode_window_minutes"], cfg["flicker_window_minutes"])
        row = {
            "meta_decision_id": f"META:MULTI:{symbol}:{side}:{stamp}", "source": "MULTI", "source_signal_ids": [v.get("signal_id") for v in variants],
            "strategy": "+".join(ids), "candidate_ids": ids, "support_count": len(ids), "symbol": symbol, "side": side,
            "day": raw.get("market_date"), "time": stamp, "contract": raw.get("contract"), "entry_ask": raw.get("entry_ask"),
            "spread_pct": spread, "market_regime": regime, "decision": decision, "block_reasons": block, "wait_reasons": wait,
            "broker_order": False, "auto_apply": False, **epi,
        }
        batch_rows.append(row); history.append(row)
    for row in batch_rows:
        t = datetime.fromisoformat(row["time"].replace("Z", "+00:00"))
        peers = [r for r in history if r is not row and r.get("source") == "MULTI" and r.get("side") == row.get("side")]
        nearby = 0
        for peer in peers:
            try:
                pt = datetime.fromisoformat(str(peer["time"]).replace("Z", "+00:00"))
            except Exception:
                continue
            if abs((pt - t).total_seconds()) <= 120:
                nearby += 1
        row["correlated_opportunity_count_2m"] = 1 + nearby
        row["correlation_exposure"] = nearby
        append_decision(state, row)
    state["source_cursors"]["multi_signals"] = len(signals)
    return len(batch_rows)


def tick(state: dict[str, Any], cfg: dict[str, Any]) -> int:
    context = current_context(state)
    paper = load_json(PAPER, {})
    h09 = load_json(H09, {})
    multi = load_json(MULTI, {})
    n = process_h01(state, cfg, paper, context)
    n += process_h09(state, cfg, h09)
    n += process_multi(state, cfg, multi)
    save(state)
    return n


def main() -> None:
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    with LOCK.open("a+") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        cfg = load_cfg(); state = load_state(cfg)
        print(f"META_LIVE_STARTED cursors={state['source_cursors']} mode={state['mode']}", flush=True)
        while True:
            n = tick(state, cfg)
            if n:
                print(f"META_LIVE_OK new={n} counters={state['counters']}", flush=True)
            time.sleep(LOOP_SECONDS)


if __name__ == "__main__":
    main()
