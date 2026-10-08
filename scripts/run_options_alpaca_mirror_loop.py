#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import time
from datetime import datetime, time as dtime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
MIRROR = ROOT / "scripts/run_options_alpaca_mirror.py"
NY = ZoneInfo("America/New_York")
INTERVAL_SECONDS = 15
OUTSIDE_WINDOW_SLEEP = 60
WINDOW_START = dtime(9, 25)
WINDOW_END = dtime(16, 5)


def in_session_window(now_utc: datetime | None = None) -> bool:
    now_utc = now_utc or datetime.now(timezone.utc)
    ny = now_utc.astimezone(NY)
    return ny.weekday() < 5 and WINDOW_START <= ny.time().replace(tzinfo=None) <= WINDOW_END


def run_once() -> int:
    p = subprocess.run(
        [PYTHON, str(MIRROR)],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    out = (p.stdout or "").strip()
    err = (p.stderr or "").strip()

    if p.returncode != 0:
        print(f"OPTIONS_ALPACA_WATCHER_ERROR rc={p.returncode}", flush=True)
        if out:
            print(out, flush=True)
        if err:
            print(err, flush=True)
        return p.returncode

    interesting = (
        "ACTION " in out
        or "MIRROR_BUSY" in out
        or "MIRROR_DISABLED" in out
        or "states={} " not in (out + " ") and "tracked=0" not in out
    )
    if interesting and out:
        print(out, flush=True)
    return 0


def main() -> int:
    print("OPTIONS_ALPACA_WATCHER_STARTED interval=15s window=09:25-16:05 America/New_York", flush=True)
    while True:
        if in_session_window():
            run_once()
            time.sleep(INTERVAL_SECONDS)
        else:
            time.sleep(OUTSIDE_WINDOW_SLEEP)


if __name__ == "__main__":
    raise SystemExit(main())
