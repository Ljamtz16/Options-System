from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta
from statistics import mean, median
from typing import Any
from zoneinfo import ZoneInfo

NY = ZoneInfo("America/New_York")


def policy_return(row: dict[str, Any], horizon: int, stop_pct: int) -> float:
    outcome = str(row.get(f"call_{horizon}m_tp10_sl{stop_pct}") or "")
    terminal = float(row.get(f"call_ret_{horizon}m") or 0.0)
    if outcome == "TP_FIRST":
        return 0.10
    if outcome == "SL_FIRST":
        return -stop_pct / 100.0
    return terminal


def stop_summary(rows: list[dict[str, Any]], horizon: int, stop_pct: int) -> dict[str, Any]:
    field = f"call_{horizon}m_tp10_sl{stop_pct}"
    counts = Counter(str(r.get(field) or "") for r in rows)
    vals = [policy_return(r, horizon, stop_pct) for r in rows]
    decided = counts.get("TP_FIRST", 0) + counts.get("SL_FIRST", 0)
    return {
        "horizon_minutes": horizon,
        "stop_pct": stop_pct,
        "n": len(rows),
        "tp_first": counts.get("TP_FIRST", 0),
        "sl_first": counts.get("SL_FIRST", 0),
        "neither": counts.get("NEITHER", 0),
        "incomplete": counts.get("", 0),
        "tp_first_rate_decided": counts.get("TP_FIRST", 0) / decided if decided else None,
        "mean_policy_return": mean(vals) if vals else None,
    }


def session_bucket(iso: str) -> str:
    dt = datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(NY)
    minute = dt.hour * 60 + dt.minute
    if minute < 11 * 60:
        return "09:30-11:00"
    if minute < 14 * 60:
        return "11:00-14:00"
    return "14:00-16:00"


def nearest_row(target: datetime, rows: list[tuple[datetime, dict[str, Any]]], max_seconds: int = 75) -> dict[str, Any] | None:
    candidates = [(abs((ts - target).total_seconds()), row) for ts, row in rows if abs((ts - target).total_seconds()) <= max_seconds]
    return min(candidates, key=lambda x: x[0])[1] if candidates else None


def basic_distribution(values: list[float]) -> dict[str, Any]:
    return {
        "n": len(values),
        "mean": mean(values) if values else None,
        "median": median(values) if values else None,
    }
