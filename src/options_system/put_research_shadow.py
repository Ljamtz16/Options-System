"""Independent, read-only PUT research. No Alpaca/order/trading imports.

Rules are heuristic candidates fixed before evaluation. Only data at or before
signal timestamp is used for decisions. Forward option outcomes are diagnostics.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Any

VERSION = "put_research_shadow_v0.1"
HYPOTHESES = ("H06_PUT_BREAKDOWN", "H07_PUT_FAILED_REBOUND", "H08_PUT_CONTINUATION")
DEFAULTS = {
    "min_history_points": 4,
    "episode_gap_minutes": 6,
    "max_spread_fraction": 0.08,
    "min_quote_size": 1,
    "horizon_minutes": 15,
    "h06_break_below_prior_low_fraction": 0.00015,
    "h06_max_5m_return": -0.0008,
    "h07_min_prior_bounce_fraction": 0.0007,
    "h07_min_rejection_fraction": 0.0007,
    "h07_max_3m_return": -0.0005,
    "h07_max_20m_return": -0.0005,
    "h08_max_15m_return": -0.0015,
    "h08_max_5m_return": -0.0005,
    "h08_max_spy_from_open": -0.001,
    "h08_max_distance_from_low": 0.0005,
}


def number(value: Any) -> float | None:
    try:
        if value is None or str(value).strip() == "":
            return None
        n = float(value)
        return n if n == n and abs(n) != float("inf") else None
    except (TypeError, ValueError):
        return None


def timestamp(row: dict[str, Any]) -> datetime:
    return datetime.fromisoformat(str(row["captured_at_utc"]).replace("Z", "+00:00"))


def _at_or_before(rows: list[dict[str, Any]], target: datetime) -> float | None:
    for row in reversed(rows):
        if timestamp(row) <= target:
            return number(row.get("spot"))
    return None


def _lookback(rows: list[dict[str, Any]], now: datetime, minutes: int) -> list[float]:
    cutoff = now - timedelta(minutes=minutes)
    return [p for row in rows if cutoff <= timestamp(row) < now if (p := number(row.get("spot"))) is not None]


def _return(rows: list[dict[str, Any]], now: datetime, current: float, minutes: int) -> float | None:
    previous = _at_or_before(rows, now - timedelta(minutes=minutes))
    return current / previous - 1 if previous and previous > 0 else None


def _quote_reason(row: dict[str, Any], cfg: dict[str, Any]) -> str | None:
    if not row.get("put_contract"):
        return "NO_PUT_CONTRACT"
    ask, bid = number(row.get("put_entry_ask")), number(row.get("put_entry_bid"))
    if ask is None or bid is None or ask <= 0 or bid <= 0 or bid > ask:
        return "INVALID_PUT_QUOTE"
    if (ask - bid) / ask > cfg["max_spread_fraction"]:
        return "PUT_SPREAD_TOO_WIDE"
    for field in ("put_entry_ask_size", "put_entry_bid_size"):
        if field in row and row[field] not in (None, "") and (number(row[field]) or 0) < cfg["min_quote_size"]:
            return "PUT_QUOTE_SIZE_TOO_SMALL"
    return None


def _market_reason(row: dict[str, Any]) -> str | None:
    for field in ("spy_from_open", "qqq_from_open", "iwm_from_open"):
        if number(row.get(field)) is None:
            return "MISSING_CROSS_MARKET"
    if number(row["qqq_from_open"]) >= 0 or number(row["iwm_from_open"]) >= 0:
        return "CROSS_MARKET_NOT_BEARISH"
    return None


def analyze(rows: list[dict[str, Any]], config: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = {**DEFAULTS, **(config or {})}
    # Historical rows can contain future labels; decisions below never access them.
    ordered = sorted(rows, key=lambda r: (r.get("decision_date", ""), r.get("captured_at_utc", "")))
    seen: dict[str, list[dict[str, Any]]] = defaultdict(list)
    counters: dict[str, Counter] = {h: Counter() for h in HYPOTHESES}
    activations: list[dict[str, Any]] = []
    for row in ordered:
        day = str(row.get("decision_date") or "")
        now = timestamp(row)
        history = seen[day]
        spot = number(row.get("spot"))
        if spot is None or spot <= 0:
            for h in HYPOTHESES:
                counters[h]["MISSING_SPOT"] += 1
            history.append(row)
            continue
        prior15 = _lookback(history, now, 15)
        prior10 = _lookback(history, now, 10)
        prior20 = _lookback(history, now, 20)
        prior30 = _lookback(history, now, 30)
        recent30 = [(timestamp(x), number(x.get("spot"))) for x in history
                    if now - timedelta(minutes=30) <= timestamp(x) < now
                    and number(x.get("spot")) is not None]
        r3 = _return(history, now, spot, 3)
        r5 = _return(history, now, spot, 5)
        r15 = _return(history, now, spot, 15)
        r20 = _return(history, now, spot, 20)
        sufficient = len(prior15) >= cfg["min_history_points"]
        base_reason = _market_reason(row) or _quote_reason(row, cfg)
        # Breakdown: new 15m low + downward impulse, confirmed by QQQ/IWM.
        h06 = (sufficient and r5 is not None and r5 <= cfg["h06_max_5m_return"]
               and spot < min(prior15) * (1 - cfg["h06_break_below_prior_low_fraction"]))
        # Failed rebound: after a negative 20m move, a prior bounce has rolled over.
        # Bounce must occur AFTER its trough, not merely share a lookback window.
        bounce = False
        if recent30:
            trough_i = min(range(len(recent30)), key=lambda i: recent30[i][1])
            later_peaks = [p for t, p in recent30[trough_i + 1:]
                           if t >= now - timedelta(minutes=10)]
            bounce = bool(later_peaks and max(later_peaks) >= recent30[trough_i][1] *
                          (1 + cfg["h07_min_prior_bounce_fraction"]))
        h07 = (sufficient and bounce and r20 is not None and r20 <= cfg["h07_max_20m_return"]
               and r3 is not None and r3 <= cfg["h07_max_3m_return"]
               and spot <= max(prior10) * (1 - cfg["h07_min_rejection_fraction"]))
        # Continuation: persistent weakness near the 15m low.
        h08 = (sufficient and r15 is not None and r15 <= cfg["h08_max_15m_return"]
               and r5 is not None and r5 <= cfg["h08_max_5m_return"]
               and number(row.get("spy_from_open")) is not None
               and number(row["spy_from_open"]) <= cfg["h08_max_spy_from_open"]
               and prior15 and spot <= min(prior15) * (1 + cfg["h08_max_distance_from_low"]))
        for hid, matched in zip(HYPOTHESES, (h06, h07, h08)):
            reason = "INSUFFICIENT_HISTORY" if not sufficient else base_reason or ("MATCH" if matched else "RULE_NOT_MET")
            counters[hid][reason] += 1
            if reason != "MATCH":
                continue
            activations.append({
                "hypothesis": hid, "decision_date": day, "captured_at_utc": row["captured_at_utc"],
                "contract": row.get("put_contract"), "spot": spot,
                "put_entry_ask": number(row.get("put_entry_ask")),
                "put_entry_bid": number(row.get("put_entry_bid")),
                "put_ret_15m": number(row.get("put_ret_15m")),
                "put_15m_tp10_sl10": row.get("put_15m_tp10_sl10"),
                "spy_5m_return": r5, "spy_15m_return": r15,
                "spy_from_open": number(row.get("spy_from_open")),
                "qqq_from_open": number(row.get("qqq_from_open")),
                "iwm_from_open": number(row.get("iwm_from_open")),
            })
        history.append(row)
    # Episode de-duplication uses activation timestamps only, not future outcomes.
    episodes = []
    latest: dict[tuple[str, str], datetime] = {}
    for row in activations:
        key = (row["hypothesis"], row["decision_date"])
        now = timestamp(row)
        if key not in latest or (now - latest[key]).total_seconds() > cfg["episode_gap_minutes"] * 60:
            episode = dict(row)
            episode["episode_id"] = f"{key[0]}:{key[1]}:P{1 + sum(e['hypothesis'] == key[0] and e['decision_date'] == key[1] for e in episodes)}"
            episodes.append(episode)
        latest[key] = now
    summary = {}
    for hid in HYPOTHESES:
        selected = [e for e in episodes if e["hypothesis"] == hid]
        valid = [e for e in selected if e["put_ret_15m"] is not None]
        returns = [e["put_ret_15m"] for e in valid]
        decisions = [e["put_15m_tp10_sl10"] for e in selected if e["put_15m_tp10_sl10"] in ("TP_FIRST", "SL_FIRST")]
        summary[hid] = {
            "snapshot_filter_counts": dict(counters[hid]), "activations": sum(e["hypothesis"] == hid for e in activations),
            "episodes": len(selected), "days_with_episodes": len({e["decision_date"] for e in selected}),
            "evaluated_15m": len(valid), "mean_put_return_15m": sum(returns)/len(returns) if returns else None,
            "positive_15m": sum(v > 0 for v in returns), "negative_15m": sum(v < 0 for v in returns),
            "tp_first": decisions.count("TP_FIRST"), "sl_first": decisions.count("SL_FIRST"),
            "diagnostic_gross_pnl_one_contract": sum(e["put_entry_ask"] * 100 * e["put_ret_15m"] for e in valid),
        }
    return {
        "version": VERSION, "mode": "RESEARCH_ONLY_NO_ORDERS", "scientific_evidence": False,
        "warning": "Historical diagnostic only; parameters not validated prospectively. No commissions, slippage beyond observed bid/ask, or buying-power checks in gross PnL.",
        "config": cfg, "rows": len(ordered), "sessions": sorted(seen),
        "summary": summary, "episodes": episodes,
    }
