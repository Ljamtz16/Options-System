from __future__ import annotations

from collections import Counter
from typing import Any


def aggregate_multisymbol_signals(signals: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[tuple[str, str, str, str], list[dict[str, Any]]] = {}
    for row in signals:
        time = str(row.get("signal_time") or row.get("captured_at_utc") or row.get("time") or "")
        day = str(row.get("market_date") or row.get("decision_date") or row.get("day") or time[:10])
        symbol = str(row.get("symbol") or "")
        side = str(row.get("side") or row.get("candidate_side") or "").upper()
        if not time or not symbol or side not in {"CALL", "PUT"}:
            continue
        groups.setdefault((day, time, symbol, side), []).append(row)

    opportunities = []
    by_symbol = Counter()
    by_side = Counter()
    support = Counter()
    for (day, time, symbol, side), rows in sorted(groups.items()):
        candidates = sorted({str(r.get("candidate_id") or r.get("strategy") or "") for r in rows if r.get("candidate_id") or r.get("strategy")})
        contracts = sorted({str(r.get("contract") or "") for r in rows if r.get("contract")})
        rec = {
            "day": day,
            "time": time,
            "symbol": symbol,
            "side": side,
            "candidate_ids": candidates,
            "support_count": len(candidates),
            "contracts": contracts,
            "evidence": "PROSPECTIVE",
            "mode": "SHADOW_AGGREGATION_ONLY",
            "broker_order": False,
        }
        opportunities.append(rec)
        by_symbol[symbol] += 1
        by_side[side] += 1
        support[len(candidates)] += 1

    return {
        "raw_signals": len(signals),
        "opportunities": len(opportunities),
        "duplicates_collapsed": max(0, len(signals) - len(opportunities)),
        "by_symbol": dict(by_symbol),
        "by_side": dict(by_side),
        "by_support_count": {str(k): v for k, v in sorted(support.items())},
        "rows": opportunities,
    }
