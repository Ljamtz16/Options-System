import csv
import json
from pathlib import Path
from datetime import datetime, timezone

from options_system.prospective_paper_trader import (
    build_paper_signals,
    replay_paper_account,
)

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / "artifacts" / "intraday"

TRACKER = ROOT / "data/processed/intraday/prospective_hypothesis_tracker_v02.csv"
FROZEN = A / "FROZEN_HYPOTHESES_V02.json"
RISK = A / "PROSPECTIVE_RISK_GATE_V01.json"
OUT = A / "PAPER_RISK_REPLAY_COMPARISON_V01.json"

FRACTIONS = [0.0, 0.2, 0.4, 0.6, 0.8]


def load_snapshots():
    rows = []

    for p in sorted((ROOT / "data/raw/prospective").glob("spy_options_*.json")):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue

        if d.get("captured_at_utc"):
            rows.append(d)

    return sorted(rows, key=lambda x: x["captured_at_utc"])


tracker_rows = (
    list(csv.DictReader(TRACKER.open(encoding="utf-8")))
    if TRACKER.exists()
    else []
)

frozen = json.loads(FROZEN.read_text(encoding="utf-8"))
official_gate = json.loads(RISK.read_text(encoding="utf-8"))

signals = build_paper_signals(
    tracker_rows,
    frozen["hypotheses"],
    frozen["frozen_at"],
)

snapshots = load_snapshots()

scenarios = {}

for fraction in FRACTIONS:
    gate = dict(official_gate)
    gate["allowed_max_fraction"] = fraction
    gate["status"] = "ACTIVE" if fraction > 0 else "BLOCKED"

    result = replay_paper_account(
        snapshots,
        signals,
        gate,
        as_of=datetime.now(timezone.utc),
        policy={
            "initial_cash": 1000.0,
            "tp": 0.10,
            "sl": -0.10,
            "max_contracts_per_trade": 1,
        },
    )

    closed = [
        x for x in result["ledger"]
        if x.get("status") == "CLOSED"
    ]

    blocked = [
        x for x in result["ledger"]
        if x.get("status") == "BLOCKED"
    ]

    tp = sum(x.get("exit_reason") == "TP10" for x in closed)
    sl = sum(x.get("exit_reason") == "SL10" for x in closed)
    horizon = sum(x.get("exit_reason") == "HORIZON" for x in closed)

    scenarios[f"pct_{int(fraction * 100)}"] = {
        "risk_fraction": fraction,
        "signals_seen": len(signals),
        "executed_trades": len(closed) + result["open_positions_count"],
        "closed_trades": len(closed),
        "open_positions": result["open_positions_count"],
        "blocked_signals": len(blocked),
        "tp10": tp,
        "sl10": sl,
        "horizon": horizon,
        "initial_cash": result["initial_cash"],
        "final_equity": result["equity"],
        "net_pnl": result["net_account_pnl"],
        "return_pct": (
            result["net_account_pnl"] / result["initial_cash"]
            if result["initial_cash"]
            else None
        ),
        "ledger": result["ledger"],
        "open_positions_detail": result["open_positions"],
    }

payload = {
    "version": "v0.2",
    "contract_selection_version":"executable_contract_v1",
    "same_captures_different_budget_can_select_different_contracts":True,
    "scientific_evidence": False,
    "purpose": "paper_trading_risk_counterfactual_only",
    "official_scientific_risk_fraction": official_gate.get(
        "allowed_max_fraction"
    ),
    "signals_seen": len(signals),
    "scenarios": scenarios,
}

OUT.write_text(
    json.dumps(payload, indent=2),
    encoding="utf-8",
)

print("PAPER_RISK_REPLAY_COMPARISON_OK")

for name, x in scenarios.items():
    print(
        name,
        "risk", x["risk_fraction"],
        "executed", x["executed_trades"],
        "blocked", x["blocked_signals"],
        "TP", x["tp10"],
        "SL", x["sl10"],
        "net", round(x["net_pnl"], 2),
        "equity", round(x["final_equity"], 2),
    )
