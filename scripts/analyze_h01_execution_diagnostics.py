#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from statistics import mean

from options_system.h01_execution_diagnostics import basic_distribution, nearest_row, policy_return, session_bucket, stop_summary

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "artifacts/intraday/PAPER_TRADING_LIVE_STATE_V01.json"
TRACKER = ROOT / "data/processed/intraday/prospective_hypothesis_tracker_v02.csv"
OUT = ROOT / "artifacts/intraday/H01_EXECUTION_DIAGNOSTICS_V01.json"

state = json.loads(STATE.read_text(encoding="utf-8"))
trades = [x for x in state.get("live_ledger") or [] if x.get("hypothesis") == "CALL_FLOW_REVERSAL_V01"]
tracker_rows = list(csv.DictReader(TRACKER.open(encoding="utf-8")))
tracker_by_time = {r["captured_at_utc"]: r for r in tracker_rows}
matched = [(t, tracker_by_time.get(t.get("signal_time"))) for t in trades]
matched = [(t, r) for t, r in matched if r]

stop_variants = {}
for horizon in (15, 30, 60):
    stop_variants[str(horizon)] = {
        "SL10": stop_summary([r for _, r in matched], horizon, 10),
        "SL20": stop_summary([r for _, r in matched], horizon, 20),
    }

mae60 = [float(r.get("call_mae_60m") or 0.0) for _, r in matched]
mfe60 = [float(r.get("call_mfe_60m") or 0.0) for _, r in matched]

by_day_rows = defaultdict(list)
for r in tracker_rows:
    try:
        ts = datetime.fromisoformat(r["captured_at_utc"].replace("Z", "+00:00"))
    except Exception:
        continue
    by_day_rows[r.get("decision_date") or ts.date().isoformat()].append((ts, r))

for rows in by_day_rows.values():
    rows.sort(key=lambda x: x[0])

delay_summary = {}
for delay in (0, 1, 3, 5, 10):
    outcomes = []
    terminals = []
    matched_delay = 0
    for trade, _ in matched:
        signal_time = str(trade.get("signal_time") or "")
        if not signal_time:
            continue
        t0 = datetime.fromisoformat(signal_time.replace("Z", "+00:00")) + timedelta(minutes=delay)
        row = nearest_row(t0, by_day_rows.get(signal_time[:10], []), 75)
        if not row:
            continue
        matched_delay += 1
        outcome = str(row.get("call_60m_tp10_sl10") or "")
        if outcome in {"TP_FIRST", "SL_FIRST"}:
            outcomes.append(outcome)
        if row.get("call_ret_60m") not in (None, ""):
            terminals.append(float(row["call_ret_60m"]))
    decided = len(outcomes)
    tp = sum(x == "TP_FIRST" for x in outcomes)
    delay_summary[str(delay)] = {
        "delay_minutes": delay,
        "matched": matched_delay,
        "decided": decided,
        "tp_first": tp,
        "sl_first": sum(x == "SL_FIRST" for x in outcomes),
        "tp_first_rate": tp / decided if decided else None,
        "mean_terminal_return_60m": mean(terminals) if terminals else None,
        "note": "Fresh representative contract at delayed snapshot; counterfactual only.",
    }

buckets = defaultdict(list)
for trade, _ in matched:
    if trade.get("status") != "CLOSED" or not trade.get("entry_time"):
        continue
    buckets[session_bucket(trade["entry_time"])].append(float(trade.get("net_pnl") or 0.0))
time_of_day = {
    key: {"n": len(vals), "net_pnl": sum(vals), "mean_net_pnl": mean(vals) if vals else None}
    for key, vals in buckets.items()
}

report = {
    "version": "H01_EXECUTION_DIAGNOSTICS_V01",
    "mode": "COUNTERFACTUAL_DIAGNOSTIC_ONLY",
    "scientific_evidence": False,
    "frozen_h01_unchanged": True,
    "auto_apply": False,
    "warning": "Do not change H01 from this report alone. Stops and delays are descriptive counterfactuals.",
    "matched_live_h01_signals": len(matched),
    "stop_variants": stop_variants,
    "path_distribution_60m": {
        "mae": basic_distribution(mae60),
        "mfe": basic_distribution(mfe60),
        "mfe_ge_10pct": sum(x >= 0.10 for x in mfe60),
        "mae_le_minus_10pct": sum(x <= -0.10 for x in mae60),
        "mae_le_minus_20pct": sum(x <= -0.20 for x in mae60),
    },
    "delayed_entry": delay_summary,
    "time_of_day_live_pnl": time_of_day,
}
OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"output": str(OUT), "matched": len(matched), "time_of_day": time_of_day}, indent=2))
