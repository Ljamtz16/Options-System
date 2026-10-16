from __future__ import annotations

from datetime import datetime
from typing import Any

VERSION = "h09_put_flow_v0.1"


def number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def timestamp(row: dict[str, Any]) -> datetime:
    return datetime.fromisoformat(str(row["captured_at_utc"]).replace("Z", "+00:00"))


def compare(value, op: str, threshold: float) -> bool:
    v = number(value)
    if v is None:
        return False
    if op == ">":
        return v > threshold
    if op == ">=":
        return v >= threshold
    if op == "<":
        return v < threshold
    if op == "<=":
        return v <= threshold
    raise ValueError(f"Unsupported op {op}")


def candidate_active(candidate: dict[str, Any], row: dict[str, Any]) -> bool:
    return all(compare(row.get(r["feature"]), r["op"], float(r["value"])) for r in candidate["rules"])


def active_candidates(config: dict[str, Any], row: dict[str, Any]) -> list[str]:
    return [c["id"] for c in config["candidates"] if candidate_active(c, row)]


def live_delta_row(previous: dict[str, Any] | None, current: dict[str, Any]) -> dict[str, Any]:
    row = dict(current)
    mapping = (
        ("atm_iv", "d_atm_iv_prev"),
        ("put_call_iv_skew", "d_put_call_iv_skew_prev"),
        ("put_call_volume_ratio_1pct", "d_put_call_volume_ratio_1pct_prev"),
    )
    for source, target in mapping:
        cur = number(current.get(source))
        prev = number(previous.get(source)) if previous else None
        row[target] = cur - prev if cur is not None and prev is not None else None
    return row


def is_new_episode(last_signal_utc: str | None, now_utc: str, gap_minutes: float) -> bool:
    if not last_signal_utc:
        return True
    gap = (datetime.fromisoformat(now_utc.replace("Z", "+00:00")) -
           datetime.fromisoformat(last_signal_utc.replace("Z", "+00:00"))).total_seconds() / 60.0
    return gap > float(gap_minutes)


def summarize(rows: list[dict[str, Any]], candidate_id: str, horizons=(15, 30, 60)) -> dict[str, Any]:
    picked = [r for r in rows if r.get("candidate_id") == candidate_id]
    out: dict[str, Any] = {"episodes": len(picked), "horizons": {}}
    for h in horizons:
        vals = [number(r.get(f"put_ret_{h}m")) for r in picked]
        vals = [v for v in vals if v is not None]
        pnl_1c = []
        for r in picked:
            entry = number(r.get("put_entry_ask"))
            ret = number(r.get(f"put_ret_{h}m"))
            if entry is not None and entry > 0 and ret is not None:
                pnl_1c.append(entry * 100.0 * ret)
        paths = [r.get(f"put_{h}m_tp10_sl10") for r in picked]
        decided = [p for p in paths if p in {"TP_FIRST", "SL_FIRST"}]
        out["horizons"][str(h)] = {
            "n": len(vals),
            "mean_return": sum(vals) / len(vals) if vals else None,
            "win_rate": sum(v > 0 for v in vals) / len(vals) if vals else None,
            "pnl_1_contract_n": len(pnl_1c),
            "total_pnl_1_contract": sum(pnl_1c) if pnl_1c else None,
            "mean_pnl_1_contract": sum(pnl_1c) / len(pnl_1c) if pnl_1c else None,
            "tp10_before_sl10_rate": sum(p == "TP_FIRST" for p in decided) / len(decided) if decided else None,
            "decided_n": len(decided),
        }
    return out
