from __future__ import annotations

from datetime import datetime, timezone

VERSION = "h09b_dre_v0.1"
SOURCE_CANDIDATE = "H09B_PUT_FLOW_MIRROR_RISKOFF_V01"


def num(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def spread_pct(bid, ask):
    bid, ask = num(bid), num(ask)
    if bid is None or ask is None or ask <= 0 or bid < 0 or bid > ask:
        return None
    return (ask - bid) / ask


def route_signal(bid, ask, cfg):
    spread = spread_pct(bid, ask)
    if spread is None:
        return {"decision": "BLOCK", "reason": "INVALID_QUOTE", "spread_pct": None}
    if spread <= float(cfg["buy_now_max_spread_pct"]):
        return {"decision": "BUY_NOW", "reason": "TIGHT_SPREAD", "spread_pct": spread}
    if spread <= float(cfg["arm_touch10_max_spread_pct"]):
        return {"decision": "ARM_TOUCH10", "reason": "MID_SPREAD_WAIT_PULLBACK", "spread_pct": spread}
    return {"decision": "BLOCK", "reason": "WIDE_SPREAD", "spread_pct": spread}


def arm_mark(initial_ask, current_bid):
    initial_ask, current_bid = num(initial_ask), num(current_bid)
    if initial_ask is None or initial_ask <= 0 or current_bid is None:
        return None
    return current_bid / initial_ask - 1.0


def touch10_triggered(initial_ask, current_bid, cfg):
    mark = arm_mark(initial_ask, current_bid)
    return bool(mark is not None and mark <= float(cfg["arm_trigger_return"]) + 1e-12), mark


def quote_for_contract(envelope, contract):
    snapshots = ((((envelope.get("payload") or {}).get("options") or {}).get("snapshot") or {}).get("snapshots") or {})
    row = snapshots.get(contract) or {}
    q = row.get("latestQuote") or {}
    bid, ask = num(q.get("bp")), num(q.get("ap"))
    if bid is None or ask is None or ask <= 0:
        return None
    return {"bid": bid, "ask": ask, "quote_time": q.get("t")}


def parse_time(value):
    return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(timezone.utc)
