#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from options_system.multisymbol_arbitration import aggregate_multisymbol_signals

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "artifacts/intraday/MULTISYMBOL_LIVE_STATE_V01.json"
OUT = ROOT / "artifacts/intraday/MULTISYMBOL_SIGNAL_ARBITRATION_V01.json"

state = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {"signals": []}
summary = aggregate_multisymbol_signals(state.get("signals") or [])
report = {
    "version": "MULTISYMBOL_SIGNAL_ARBITRATION_V01",
    "mode": "SHADOW_AGGREGATION_ONLY",
    "scientific_evidence": False,
    "auto_apply": False,
    "broker_orders_enabled": False,
    "policy": "DEDUPE_EXACT_SNAPSHOT_SYMBOL_SIDE_WITHOUT_RANKING",
    "summary": {k: v for k, v in summary.items() if k != "rows"},
    "rows": summary["rows"],
}
OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report["summary"], indent=2))
