from __future__ import annotations

from typing import Any

CHECKPOINT_SECONDS = (15, 30, 60, 120, 180, 300)


def record_path_checkpoints(position: dict[str, Any], *, elapsed_seconds: float, bid: float,
                            return_pct: float, quote_time: str | None, mark_time: str) -> int:
    """Persist first live quote observed at/after each path checkpoint. Telemetry only."""
    points = position.setdefault("path_checkpoints", {})
    added = 0
    for target in CHECKPOINT_SECONDS:
        key = f"{target}s"
        if elapsed_seconds < target or key in points:
            continue
        points[key] = {
            "target_seconds": target,
            "observed_elapsed_seconds": elapsed_seconds,
            "bid": bid,
            "return": return_pct,
            "quote_time": quote_time,
            "mark_time": mark_time,
        }
        added += 1
    return added
