from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from .intraday_contracts import representative_contracts
from .put_research_shadow import (
    DEFAULTS,
    _lookback,
    _market_reason,
    _quote_reason,
    _return,
    number,
    timestamp,
)

VERSION = "put_confirmation_live_v0.2"


def snapshot_to_live_row(envelope: dict[str, Any]) -> dict[str, Any]:
    payload = envelope["payload"]
    captured = str(envelope["captured_at_utc"])
    research = payload.get("research_state") or {}
    features = research.get("features") or {}
    day = str(features.get("decision_date") or "")
    if not day:
        raise ValueError("Snapshot missing decision_date")

    underlying = (payload.get("underlying") or {}).get("snapshot") or {}
    trade = underlying.get("latestTrade") or {}
    quote = underlying.get("latestQuote") or {}
    spot = trade.get("p")
    if not spot:
        bid, ask = quote.get("bp"), quote.get("ap")
        if bid and ask:
            spot = (float(bid) + float(ask)) / 2.0
    spot = number(spot)
    if spot is None or spot <= 0:
        raise ValueError("Snapshot missing valid SPY spot")

    cross = ((payload.get("cross_market") or {}).get("features") or {})
    chain = (payload.get("options") or {}).get("snapshot") or {}
    put = representative_contracts(chain, date.fromisoformat(day)).get("put")

    row = {
        "capture_id": envelope.get("capture_id"),
        "captured_at_utc": captured,
        "decision_date": day,
        "spot": spot,
        "spy_from_open": number(cross.get("spy_from_open")),
        "qqq_from_open": number(cross.get("qqq_from_open")),
        "iwm_from_open": number(cross.get("iwm_from_open")),
        "put_contract": put.get("symbol") if put else None,
        "put_entry_bid": number(put.get("bid")) if put else None,
        "put_entry_ask": number(put.get("ask")) if put else None,
        "put_entry_bid_size": number(put.get("bid_size")) if put else None,
        "put_entry_ask_size": number(put.get("ask_size")) if put else None,
    }
    return row


def h06_match(row: dict[str, Any], history: list[dict[str, Any]], config: dict[str, Any] | None = None) -> tuple[bool, str]:
    cfg = {**DEFAULTS, **(config or {})}
    now = timestamp(row)
    spot = number(row.get("spot"))
    if spot is None or spot <= 0:
        return False, "MISSING_SPOT"

    prior15 = _lookback(history, now, 15)
    if len(prior15) < cfg["min_history_points"]:
        return False, "INSUFFICIENT_HISTORY"

    reason = _market_reason(row) or _quote_reason(row, cfg)
    if reason:
        return False, reason

    r5 = _return(history, now, spot, 5)
    if r5 is None:
        return False, "MISSING_5M_RETURN"
    if r5 > cfg["h06_max_5m_return"]:
        return False, "5M_IMPULSE_NOT_BEARISH"

    threshold = min(prior15) * (1 - cfg["h06_break_below_prior_low_fraction"])
    if spot >= threshold:
        return False, "NO_15M_BREAKDOWN"

    return True, "MATCH"


def expire_machine(machine: dict[str, Any], now: datetime, v02: dict[str, Any]) -> dict[str, Any] | None:
    locked = machine.get("locked_until_utc")
    if locked and now >= datetime.fromisoformat(str(locked).replace("Z", "+00:00")):
        machine["locked_until_utc"] = None
        machine["status"] = "IDLE"
        return {"event": "UNLOCK", "at_utc": now.isoformat()}

    arm = machine.get("arm")
    if arm:
        gap = (now - timestamp(arm)).total_seconds() / 60.0
        max_minutes = float(v02["state_machine"]["confirmation_max_minutes"])
        if gap > max_minutes:
            machine["arm"] = None
            machine["status"] = "IDLE"
            return {
                "event": "ARM_EXPIRED",
                "at_utc": now.isoformat(),
                "armed_at_utc": arm["captured_at_utc"],
                "age_minutes": gap,
            }
    return None


def apply_h06_activation(machine: dict[str, Any], row: dict[str, Any], v02: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any] | None]:
    now = timestamp(row)
    sm = v02["state_machine"]

    locked = machine.get("locked_until_utc")
    if locked and now < datetime.fromisoformat(str(locked).replace("Z", "+00:00")):
        return {"event": "H06_IGNORED_LOCKED", "at_utc": row["captured_at_utc"]}, None

    arm = machine.get("arm")
    if arm is None:
        machine["arm"] = dict(row)
        machine["status"] = "ARMED"
        return {
            "event": "ARMED",
            "at_utc": row["captured_at_utc"],
            "spot": row.get("spot"),
            "contract": row.get("put_contract"),
        }, None

    gap = (now - timestamp(arm)).total_seconds() / 60.0
    min_minutes = float(sm["confirmation_min_minutes"])
    max_minutes = float(sm["confirmation_max_minutes"])

    if gap < min_minutes:
        return {
            "event": "H06_EARLY",
            "at_utc": row["captured_at_utc"],
            "gap_minutes": gap,
        }, None

    if gap > max_minutes:
        machine["arm"] = dict(row)
        machine["status"] = "ARMED"
        return {
            "event": "REARMED",
            "at_utc": row["captured_at_utc"],
            "prior_armed_at_utc": arm["captured_at_utc"],
            "gap_minutes": gap,
        }, None

    fields = ("spy_from_open", "qqq_from_open", "iwm_from_open")
    if any(arm.get(field) is None or row.get(field) is None for field in fields):
        return {
            "event": "CONFIRM_REJECT_MISSING_CROSS_MARKET",
            "at_utc": row["captured_at_utc"],
            "gap_minutes": gap,
        }, None

    comparisons = {field: row[field] < arm[field] for field in fields}
    if not all(comparisons.values()):
        return {
            "event": "CONFIRM_REJECT_ALL3",
            "at_utc": row["captured_at_utc"],
            "gap_minutes": gap,
            "comparisons": comparisons,
        }, None

    signal = {
        "decision_date": row["decision_date"],
        "armed_at_utc": arm["captured_at_utc"],
        "confirmed_at_utc": row["captured_at_utc"],
        "confirmation_gap_minutes": gap,
        "arm": dict(arm),
        "entry": dict(row),
    }
    machine["arm"] = None
    machine["status"] = "LOCKED"
    machine["locked_until_utc"] = (now + timedelta(minutes=float(sm["post_signal_lock_minutes"]))).isoformat()
    return {
        "event": "CONFIRMED",
        "at_utc": row["captured_at_utc"],
        "gap_minutes": gap,
        "contract": row.get("put_contract"),
    }, signal
