from __future__ import annotations

from datetime import datetime
from typing import Any

from .prospective_hypothesis_tracker import hypothesis_active

VERSION = "frozen_hypotheses_live_v0.1"
H03_ID = "H03_CALL_RELATIVE_WEAKNESS_REVERSAL_V01"
DEFAULT_EPISODE_GAP_MINUTES = 6.0


def number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def stamp(value: str) -> datetime:
    out = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if out.tzinfo is None:
        raise ValueError("Timezone required")
    return out


def open_reference_values(envelope: dict[str, Any]) -> dict[str, float | None]:
    payload = envelope.get("payload") or {}
    underlying = (payload.get("underlying") or {}).get("snapshot") or {}
    cross = (payload.get("cross_market") or {}).get("snapshots") or {}

    def daily_open(snapshot):
        return number((snapshot.get("dailyBar") or {}).get("o"))

    return {
        "SPY": daily_open(underlying),
        "QQQ": daily_open(cross.get("QQQ") or {}),
        "IWM": daily_open(cross.get("IWM") or {}),
    }


def open_reference_stable(previous: dict[str, Any] | None, current: dict[str, Any]) -> tuple[bool, str]:
    if not previous:
        return False, "NO_PREVIOUS_CAPTURE"
    if previous.get("decision_date") != current.get("decision_date"):
        return False, "SESSION_NOT_STABILIZED"

    prev_refs = previous.get("open_refs") or {}
    cur_refs = current.get("open_refs") or {}
    for symbol in ("SPY", "QQQ", "IWM"):
        a, b = number(prev_refs.get(symbol)), number(cur_refs.get(symbol))
        if a is None or b is None or a <= 0 or b <= 0:
            return False, f"MISSING_{symbol}_OPEN_REFERENCE"
        tolerance = max(1e-8, abs(a) * 1e-9)
        if abs(a - b) > tolerance:
            return False, f"UNSTABLE_{symbol}_OPEN_REFERENCE"
    return True, "STABLE"


def add_previous_deltas(row: dict[str, Any], previous: dict[str, Any] | None) -> dict[str, Any]:
    out = dict(row)
    for field in ("atm_iv", "put_call_iv_skew", "put_call_volume_ratio_1pct"):
        cur = number(out.get(field))
        prev = number((previous or {}).get(field))
        out[f"d_{field}_prev"] = cur - prev if cur is not None and prev is not None else None
    return out


def live_hypothesis_active(hypothesis: dict[str, Any], row: dict[str, Any], *, h03_open_stable: bool) -> tuple[bool, str]:
    if hypothesis.get("id") == H03_ID and not h03_open_stable:
        return False, "H03_OPEN_REFERENCE_UNSTABLE"
    return hypothesis_active(hypothesis, row), "RULES"


def fresh_episode_state() -> dict[str, Any]:
    return {"decision_date": None, "last_activation_utc": None, "next_index": 1}


def episode_activation(episode: dict[str, Any] | None, hypothesis: dict[str, Any], row: dict[str, Any]) -> tuple[dict[str, Any], str | None]:
    state = dict(episode or fresh_episode_state())
    day = str(row["decision_date"])
    now = stamp(row["captured_at_utc"])
    gap_limit = float((hypothesis.get("episode_policy") or {}).get("gap_minutes", DEFAULT_EPISODE_GAP_MINUTES))

    if state.get("decision_date") != day:
        state = fresh_episode_state()
        state["decision_date"] = day

    previous = state.get("last_activation_utc")
    new_episode = previous is None
    if previous is not None:
        new_episode = (now - stamp(previous)).total_seconds() > gap_limit * 60.0

    state["last_activation_utc"] = row["captured_at_utc"]
    if not new_episode:
        return state, None

    index = int(state.get("next_index") or 1)
    state["next_index"] = index + 1
    return state, f"{hypothesis['id']}:{day}:P{index}"


def signal_from_row(hypothesis: dict[str, Any], row: dict[str, Any], signal_id: str) -> dict[str, Any]:
    side = str(hypothesis["side"]).lower()
    return {
        "signal_id": signal_id,
        "hypothesis": hypothesis["id"],
        "decision_date": row["decision_date"],
        "signal_time": row["captured_at_utc"],
        "activation_count": 1,
        "side": side,
        "horizon_min": int(hypothesis["horizon_min"]),
        "contract": row.get(f"{side}_contract"),
        "entry_ask": row.get(f"{side}_entry_ask"),
        "entry_bid": row.get(f"{side}_entry_bid"),
        "entry_ask_size": row.get(f"{side}_entry_ask_size"),
        "entry_bid_size": row.get(f"{side}_entry_bid_size"),
    }


def compact_feature_memory(row: dict[str, Any], envelope: dict[str, Any]) -> dict[str, Any]:
    return {
        "decision_date": row.get("decision_date"),
        "captured_at_utc": row.get("captured_at_utc"),
        "atm_iv": row.get("atm_iv"),
        "put_call_iv_skew": row.get("put_call_iv_skew"),
        "put_call_volume_ratio_1pct": row.get("put_call_volume_ratio_1pct"),
        "open_refs": open_reference_values(envelope),
    }
