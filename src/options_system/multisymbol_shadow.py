from __future__ import annotations

from datetime import datetime
from typing import Any

VERSION = "multisymbol_shadow_v0.1"


def number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def stamp(value: str) -> datetime:
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def compare(value, op: str, threshold: float) -> bool:
    v = number(value)
    if v is None:
        return False
    if op == ">": return v > threshold
    if op == ">=": return v >= threshold
    if op == "<": return v < threshold
    if op == "<=": return v <= threshold
    raise ValueError(f"Unsupported op {op}")


def candidate_active(candidate: dict[str, Any], row: dict[str, Any]) -> bool:
    return all(compare(row.get(r["feature"]), r["op"], float(r["value"])) for r in candidate["rules"])


def closest_lookback(history: list[dict[str, Any]], now: datetime, minutes: float = 5.0) -> dict[str, Any] | None:
    eligible = []
    for row in history:
        age = (now - stamp(row["captured_at_utc"])).total_seconds() / 60.0
        if 3.5 <= age <= 8.0:
            eligible.append((abs(age - minutes), row))
    return min(eligible, key=lambda x: x[0])[1] if eligible else None


def derive_row(
    base: dict[str, Any],
    first_spot: float | None,
    history: list[dict[str, Any]],
    market_first: dict[str, float] | None = None,
) -> dict[str, Any]:
    row = dict(base)
    spot = number(row.get("spot"))
    now = stamp(row["captured_at_utc"])
    if spot is None or spot <= 0:
        row["own_from_first"] = None
        row["own_return_5m"] = None
        row["relative_to_spy"] = None
        return row

    row["own_from_first"] = spot / first_spot - 1.0 if first_spot else 0.0
    prior = closest_lookback(history, now, 5.0)
    prior_spot = number(prior.get("spot")) if prior else None
    row["own_return_5m"] = spot / prior_spot - 1.0 if prior_spot else None

    market_first = market_first or {}
    for sym in ("spy", "qqq", "iwm"):
        price = number(row.get(f"market_{sym}_price"))
        first = number(market_first.get(sym.upper()))
        row[f"market_{sym}_from_first"] = price / first - 1.0 if price and first else None

    spy_move = number(row.get("market_spy_from_first"))
    row["relative_to_spy"] = 0.0 if row.get("symbol") == "SPY" else (
        row["own_from_first"] - spy_move if spy_move is not None else None
    )
    return row


def active_candidates(config: dict[str, Any], row: dict[str, Any]) -> list[dict[str, Any]]:
    return [c for c in config["candidates"] if candidate_active(c, row)]


def is_new_episode(last_signal_utc: str | None, now_utc: str, gap_minutes: float) -> bool:
    if not last_signal_utc:
        return True
    gap = (stamp(now_utc) - stamp(last_signal_utc)).total_seconds() / 60.0
    return gap > float(gap_minutes)


def _max_drawdown_pnl(pnls: list[float]) -> float | None:
    if not pnls:
        return None
    equity = 0.0
    peak = 0.0
    worst = 0.0
    for pnl in pnls:
        equity += pnl
        peak = max(peak, equity)
        worst = min(worst, equity - peak)
    return worst


def summarize_episodes(rows: list[dict[str, Any]], candidate: dict[str, Any], horizons=(15, 30, 60)) -> dict[str, Any]:
    cid, side = candidate["id"], candidate["side"].lower()
    selected = sorted([r for r in rows if r.get("candidate_id") == cid], key=lambda r: r.get("captured_at_utc") or "")
    result: dict[str, Any] = {"episodes": len(selected), "horizons": {}}
    for h in horizons:
        vals = [number(r.get(f"{side}_terminal_return_{h}m")) for r in selected]
        vals = [v for v in vals if v is not None]
        pnl_1c = []
        mfe_pnl_1c = []
        mae_pnl_1c = []
        for r in selected:
            entry = number(r.get(f"entry_{side}_ask"))
            ret = number(r.get(f"{side}_terminal_return_{h}m"))
            mfe = number(r.get(f"{side}_best_return_{h}m"))
            mae = number(r.get(f"{side}_worst_return_{h}m"))
            if entry is not None and entry > 0 and ret is not None:
                pnl_1c.append(entry * 100.0 * ret)
            if entry is not None and entry > 0 and mfe is not None:
                mfe_pnl_1c.append(entry * 100.0 * mfe)
            if entry is not None and entry > 0 and mae is not None:
                mae_pnl_1c.append(entry * 100.0 * mae)
        best = [number(r.get(f"{side}_best_return_{h}m")) for r in selected]
        best = [v for v in best if v is not None]
        worst = [number(r.get(f"{side}_worst_return_{h}m")) for r in selected]
        worst = [v for v in worst if v is not None]
        paths = [r.get(f"{side}_{h}m_tp10_sl10") for r in selected]
        decided = [p for p in paths if p in {"TP_FIRST", "SL_FIRST"}]
        result["horizons"][str(h)] = {
            "n": len(vals),
            "mean_return": sum(vals) / len(vals) if vals else None,
            "win_rate": sum(v > 0 for v in vals) / len(vals) if vals else None,
            "pnl_1_contract_n": len(pnl_1c),
            "total_pnl_1_contract": sum(pnl_1c) if pnl_1c else None,
            "mean_pnl_1_contract": sum(pnl_1c) / len(pnl_1c) if pnl_1c else None,
            "mean_mfe_pnl_1_contract": sum(mfe_pnl_1c) / len(mfe_pnl_1c) if mfe_pnl_1c else None,
            "mean_mae_pnl_1_contract": sum(mae_pnl_1c) / len(mae_pnl_1c) if mae_pnl_1c else None,
            "max_drawdown_pnl_1_contract": _max_drawdown_pnl(pnl_1c),
            "mean_mfe": sum(best) / len(best) if best else None,
            "mean_mae": sum(worst) / len(worst) if worst else None,
            "tp10_before_sl10_rate": sum(p == "TP_FIRST" for p in decided) / len(decided) if decided else None,
            "decided_n": len(decided),
        }
    return result


def signal_key(candidate_id: str, symbol: str) -> str:
    return f"{candidate_id}|{symbol}"
