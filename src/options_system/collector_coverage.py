from __future__ import annotations

import json
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from .session_cache import atomic_text

VERSION = "collector_coverage_v0.1"


def record_collector_event(summary_path, events_path, event):
    summary_path = Path(summary_path)
    events_path = Path(events_path)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    events_path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(event)
    payload.setdefault("recorded_at_utc", datetime.now(timezone.utc).isoformat())
    payload.setdefault("collector", "SPY_PROSPECTIVE")
    day = str(payload["decision_date"])
    try:
        root = json.loads(summary_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        root = {"version": VERSION, "days": {}}
    d = root.setdefault("days", {}).setdefault(day, {
        "attempts": 0, "successes": 0, "failures": 0,
        "armed_failures": 0, "failure_types": {}, "last_event_utc": None,
    })
    d["attempts"] += 1
    if payload.get("success"):
        d["successes"] += 1
    else:
        d["failures"] += 1
        if payload.get("put_machine_status") == "ARMED":
            d["armed_failures"] += 1
        failure_type = str(payload.get("error_type") or "UNKNOWN")
        counts = Counter(d.get("failure_types") or {})
        counts[failure_type] += 1
        d["failure_types"] = dict(counts)
    d["coverage_rate"] = d["successes"] / d["attempts"] if d["attempts"] else None
    d["last_event_utc"] = payload["recorded_at_utc"]
    root["updated_at_utc"] = payload["recorded_at_utc"]
    atomic_text(summary_path, json.dumps(root, indent=2) + "\n")
    with events_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, sort_keys=True) + "\n")
    return d


def classify_error(text):
    lower = str(text).lower()
    if "http error 400" in lower: return "HTTP_400"
    if "http error 429" in lower: return "HTTP_429"
    if "timed out" in lower or "timeout" in lower: return "TIMEOUT"
    if "http error 5" in lower: return "HTTP_5XX"
    return "COLLECTOR_ERROR"


class CollectorRunGuard:
    """Record exactly one success/failure for a market-open collector invocation."""
    def __init__(self, summary_path, events_path, put_state_path):
        self.summary_path = Path(summary_path)
        self.events_path = Path(events_path)
        self.put_state_path = Path(put_state_path)
        self.started = time.monotonic()
        self.day = None
        self.done = False
        self.previous_hook = sys.excepthook
        sys.excepthook = self._hook

    def arm(self, decision_date):
        self.day = str(decision_date)

    def _put_context(self):
        try:
            state = json.loads(self.put_state_path.read_text(encoding="utf-8"))
            machine = state.get("machine") or {}
            arm = machine.get("arm") or {}
            return machine.get("status"), arm.get("captured_at_utc")
        except (OSError, ValueError):
            return None, None

    def _record(self, success, error_type=None):
        if self.done or not self.day:
            return
        status, armed_at = self._put_context()
        record_collector_event(self.summary_path, self.events_path, {
            "decision_date": self.day,
            "success": bool(success),
            "runtime_seconds": round(time.monotonic() - self.started, 3),
            "put_machine_status": status,
            "put_armed_at_utc": armed_at,
            "error_type": error_type,
        })
        self.done = True

    def success(self):
        self._record(True)

    def _hook(self, exc_type, exc, tb):
        self._record(False, classify_error(f"{exc_type.__name__}: {exc}"))
        self.previous_hook(exc_type, exc, tb)
