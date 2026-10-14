#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / "artifacts/intraday"
STATE = A / "PUT_CONFIRM_LIVE_STATE_V02.json"
TRACKER = ROOT / "data/processed/intraday/prospective_hypothesis_tracker_v02.csv"
OUT = A / "PUT_EXECUTION_DIAGNOSTICS_V01.json"
DELAYS = (0, 3, 6)
VARIANTS = (
    "put_15m_tp10_sl10",
    "put_15m_tp10_sl20",
    "put_15m_tp20_sl10",
    "put_15m_tp20_sl20",
)


def dt(value):
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def num(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def nearest(rows, target, tolerance_seconds=90):
    candidates = []
    for row in rows:
        if row.get("decision_date") != target.date().isoformat():
            continue
        delta = abs((dt(row["captured_at_utc"]) - target).total_seconds())
        if delta <= tolerance_seconds:
            candidates.append((delta, row))
    return min(candidates, key=lambda x: x[0])[1] if candidates else None


def main():
    live = json.loads(STATE.read_text(encoding="utf-8"))
    with TRACKER.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    signals = []
    for signal in live.get("signals") or []:
        base_time = dt(signal["signal_time"])
        rec = {
            "signal_id": signal["signal_id"],
            "signal_time": signal["signal_time"],
            "contract": signal.get("contract"),
            "live_outcome": None,
            "frozen_snapshot_diagnostic": None,
            "alternative_entry_snapshots": [],
        }
        live_row = next((x for x in live.get("live_ledger") or [] if x.get("signal_id") == signal["signal_id"]), None)
        if live_row:
            rec["live_outcome"] = {k: live_row.get(k) for k in (
                "status", "entry_ask", "exit_bid", "exit_reason", "mfe", "mae", "net_pnl",
            )}

        base = nearest(rows, base_time)
        if base:
            rec["frozen_snapshot_diagnostic"] = {
                "matched_at_utc": base.get("captured_at_utc"),
                "entry_ask": num(base.get("put_entry_ask")),
                "ret_15m": num(base.get("put_ret_15m")),
                "mfe_15m": num(base.get("put_mfe_15m")),
                "mae_15m": num(base.get("put_mae_15m")),
                **{name: base.get(name) for name in VARIANTS},
            }

        for delay in DELAYS[1:]:
            target = base_time + timedelta(minutes=delay)
            row = nearest(rows, target)
            rec["alternative_entry_snapshots"].append({
                "delay_minutes": delay,
                "matched_at_utc": row.get("captured_at_utc") if row else None,
                "contract": row.get("put_contract") if row else None,
                "entry_ask": num(row.get("put_entry_ask")) if row else None,
                "ret_15m": num(row.get("put_ret_15m")) if row else None,
                "mfe_15m": num(row.get("put_mfe_15m")) if row else None,
                "mae_15m": num(row.get("put_mae_15m")) if row else None,
                "tp10_sl10": row.get("put_15m_tp10_sl10") if row else None,
            })
        signals.append(rec)

    variant_summary = {}
    for name in VARIANTS:
        vals = [((s.get("frozen_snapshot_diagnostic") or {}).get(name)) for s in signals]
        vals = [x for x in vals if x]
        variant_summary[name] = {
            "n": len(vals),
            "tp_first": sum(x == "TP_FIRST" for x in vals),
            "sl_first": sum(x == "SL_FIRST" for x in vals),
            "neither": sum(x not in ("TP_FIRST", "SL_FIRST") for x in vals),
        }

    delay_summary = {}
    for delay in DELAYS[1:]:
        vals = [x for s in signals for x in s["alternative_entry_snapshots"] if x["delay_minutes"] == delay and x.get("tp10_sl10")]
        delay_summary[str(delay)] = {
            "n": len(vals),
            "tp_first": sum(x["tp10_sl10"] == "TP_FIRST" for x in vals),
            "sl_first": sum(x["tp10_sl10"] == "SL_FIRST" for x in vals),
            "mean_ret_15m": (sum(x["ret_15m"] for x in vals if x["ret_15m"] is not None) /
                             max(1, sum(x["ret_15m"] is not None for x in vals))) if vals else None,
        }

    report = {
        "version": "PUT_EXECUTION_DIAGNOSTICS_V01",
        "mode": "COUNTERFACTUAL_DIAGNOSTIC_ONLY",
        "scientific_evidence": False,
        "frozen_put_v02_unchanged": True,
        "auto_apply": False,
        "warning": "Do not tune or promote PUT v0.2 from this report. Alternative stops/delays are descriptive diagnostics only.",
        "signals": signals,
        "stop_variant_summary": variant_summary,
        "delay_snapshot_summary": delay_summary,
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({
        "signals": len(signals),
        "stop_variant_summary": variant_summary,
        "delay_snapshot_summary": delay_summary,
        "output": str(OUT),
    }, indent=2))


if __name__ == "__main__":
    main()
