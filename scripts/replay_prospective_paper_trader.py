import csv
import json
from pathlib import Path
from datetime import datetime,timezone

from options_system.prospective_paper_trader import (
    build_paper_signals,
    replay_paper_account,
)

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / "artifacts" / "intraday"

TRACKER = ROOT / "data/processed/intraday/prospective_hypothesis_tracker_v02.csv"
FROZEN = A / "FROZEN_HYPOTHESES_V02.json"
RISK = A / "PROSPECTIVE_RISK_GATE_V01.json"
OUT = A / "PAPER_TRADING_REPLAY_V01.json"

tracker_rows = (
    list(csv.DictReader(TRACKER.open(encoding="utf-8")))
    if TRACKER.exists()
    else []
)

frozen = json.loads(FROZEN.read_text(encoding="utf-8"))
risk = json.loads(RISK.read_text(encoding="utf-8"))

snapshots = []

for p in sorted((ROOT / "data/raw/prospective").glob("spy_options_*.json")):
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        continue

    if d.get("captured_at_utc"):
        snapshots.append(d)

signals = build_paper_signals(
    tracker_rows,
    frozen["hypotheses"],
    frozen["frozen_at"],
)

result = replay_paper_account(
    snapshots,
    signals,
    risk,
    as_of=datetime.now(timezone.utc),
)

result["signals_seen"] = len(signals)

OUT.write_text(
    json.dumps(result, indent=2),
    encoding="utf-8",
)

print(
    "PAPER_REPLAY_OK",
    "signals", len(signals),
    "closed", result["closed_trades"],
    "blocked", result["blocked_signals"],
    "open", result["open_positions_count"],
    "cash", round(result["cash"], 2),
    "equity", round(result["equity"], 2),
    "net", round(result["net_account_pnl"], 2),
)
