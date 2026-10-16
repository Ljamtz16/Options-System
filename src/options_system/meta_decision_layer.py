from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from statistics import mean
from typing import Any


def num(v: Any) -> float | None:
    try:
        if v in (None, ""):
            return None
        return float(v)
    except (TypeError, ValueError):
        return None


def dt(v: str) -> datetime:
    return datetime.fromisoformat(str(v).replace("Z", "+00:00"))


def partition(day: str, cutoff: str) -> str:
    return "DISCOVERY" if str(day) <= cutoff else "PROSPECTIVE"


def market_regime(spy: Any, qqq: Any, iwm: Any) -> str:
    vals = [num(spy), num(qqq), num(iwm)]
    if any(v is None for v in vals):
        return "UNKNOWN"
    if all(v > 0 for v in vals):
        return "RISK_ON"
    if all(v < 0 for v in vals):
        return "RISK_OFF"
    return "MIXED"


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    outcomes = [num(r.get("outcome_return")) for r in rows]
    outcomes = [v for v in outcomes if v is not None]
    return {
        "n": len(rows),
        "accept": sum(r.get("decision") == "ACCEPT" for r in rows),
        "wait": sum(r.get("decision") == "WAIT" for r in rows),
        "block": sum(r.get("decision") == "BLOCK" for r in rows),
        "mean_outcome_return": mean(outcomes) if outcomes else None,
        "positive_rate": sum(v > 0 for v in outcomes) / len(outcomes) if outcomes else None,
    }


def annotate_episode_metrics(rows: list[dict[str, Any]], gap_minutes: int = 15, flicker_minutes: int = 30) -> None:
    by_key: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_key[(str(row.get("source")), str(row.get("symbol")))].append(row)
    for (source, symbol), group in by_key.items():
        group.sort(key=lambda r: dt(r["time"]))
        episode_no = 0
        episode_start = None
        episode_side = None
        episode_obs = 0
        recent: list[dict[str, Any]] = []
        previous_time = None
        for row in group:
            now = dt(row["time"])
            side = str(row.get("side") or "NONE").upper()
            new_episode = previous_time is None or (now - previous_time).total_seconds() > gap_minutes * 60 or side != episode_side
            if new_episode:
                episode_no += 1
                episode_start = now
                episode_side = side
                episode_obs = 1
            else:
                episode_obs += 1
            recent = [r for r in recent if (now - dt(r["time"])).total_seconds() <= flicker_minutes * 60]
            seq = recent + [row]
            flip_count = 0
            for a, b in zip(seq, seq[1:]):
                if str(a.get("side") or "NONE").upper() != str(b.get("side") or "NONE").upper():
                    flip_count += 1
            row["episode_id"] = f"{source}:{symbol}:{now.date().isoformat()}:E{episode_no}"
            row["persistence_observations"] = episode_obs
            row["persistence_minutes"] = round((now - episode_start).total_seconds() / 60.0, 3) if episode_start else 0.0
            row["is_episode_repeat"] = episode_obs > 1
            row["signal_flip_count_30m"] = flip_count
            row["persistence_basis"] = "candidate_activations"
            recent.append(row)
            previous_time = now


def multi_correlation_exposure(rows: list[dict[str, Any]], window_seconds: int = 120) -> None:
    ordered = sorted([r for r in rows if r.get("source") == "MULTI"], key=lambda r: dt(r["time"]))
    for row in ordered:
        now = dt(row["time"])
        side = row.get("side")
        peers = [r for r in ordered if r is not row and r.get("side") == side and abs((dt(r["time"]) - now).total_seconds()) <= window_seconds]
        row["correlated_opportunity_count_2m"] = 1 + len(peers)
        row["correlation_exposure"] = max(0, len(peers))


def decision_from_reasons(block: list[str], wait: list[str]) -> str:
    if block:
        return "BLOCK"
    if wait:
        return "WAIT"
    return "ACCEPT"
