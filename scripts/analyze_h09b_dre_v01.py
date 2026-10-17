#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from options_system.h09b_dre import SOURCE_CANDIDATE, route_signal
from options_system.session_cache import atomic_text

ROOT = Path(__file__).resolve().parents[1]
CFG = ROOT / "config/h09b_dre_v01.json"
H09 = ROOT / "artifacts/intraday/H09_PUT_FLOW_PROSPECTIVE_V01.json"
RECOVERY = ROOT / "artifacts/intraday/SL_FIRST_RECOVERY_STUDY_V01.json"
OUT = ROOT / "artifacts/intraday/H09B_DRE_REPLAY_V01.json"


def max_dd(values):
    equity = peak = worst = 0.0
    for value in values:
        equity += float(value)
        peak = max(peak, equity)
        worst = min(worst, equity - peak)
    return worst


def stats(rows, pnl_key="pnl"):
    trades = [r for r in rows if r.get(pnl_key) is not None]
    pnls = [float(r[pnl_key]) for r in trades]
    return {
        "signals": len(rows), "trades": len(trades), "skipped": len(rows) - len(trades),
        "wins": sum(v > 0 for v in pnls),
        "win_rate": (sum(v > 0 for v in pnls) / len(pnls)) if pnls else None,
        "total_pnl_1_contract": sum(pnls),
        "mean_pnl_1_contract": (sum(pnls) / len(pnls)) if pnls else None,
        "max_drawdown_pnl": max_dd(pnls),
    }


def main():
    cfg = json.loads(CFG.read_text())
    h09 = json.loads(H09.read_text())
    recovery = json.loads(RECOVERY.read_text())
    joined = []
    for evidence, section in (("DISCOVERY", "discovery"), ("PROSPECTIVE", "prospective")):
        idx = {(r.get("captured_at_utc"), r.get("put_contract")): r for r in h09[section]["rows"] if r.get("candidate_id") == SOURCE_CANDIDATE}
        for ep in recovery.get("episodes", []):
            if ep.get("strategy") != SOURCE_CANDIDATE or ep.get("evidence") != evidence or not ep.get("evaluable"):
                continue
            src = idx.get((ep.get("signal_time"), ep.get("contract")))
            if not src:
                continue
            route = route_signal(src.get("put_entry_bid"), src.get("put_entry_ask"), cfg)
            original = (ep.get("variants") or {}).get("ORIGINAL") or {}
            touch = (ep.get("variants") or {}).get("TOUCH10") or {}
            rebound = (ep.get("variants") or {}).get("REBOUND5") or {}
            decision = route["decision"]
            primary = original.get("pnl_1_contract") if decision == "BUY_NOW" else touch.get("pnl_1_contract") if decision == "ARM_TOUCH10" else None
            secondary = original.get("pnl_1_contract") if decision == "BUY_NOW" else rebound.get("pnl_1_contract") if decision == "ARM_TOUCH10" else None
            gate075 = original.get("pnl_1_contract") if route.get("spread_pct") is not None and route["spread_pct"] <= cfg["arm_touch10_max_spread_pct"] else None
            joined.append({
                "evidence": evidence, "day": ep["signal_time"][:10], "signal_time": ep["signal_time"], "contract": ep["contract"],
                "spread_pct": route.get("spread_pct"), "decision": decision, "reason": route["reason"],
                "touched_sl10": ep.get("touched_sl10"), "post_sl_hit_10": ep.get("post_sl_hit_10"),
                "original_pnl": original.get("pnl_1_contract"), "primary_pnl": primary, "secondary_pnl": secondary, "gate075_pnl": gate075,
            })
    joined.sort(key=lambda r: r["signal_time"])
    by_day = []
    for day in sorted(set(r["day"] for r in joined)):
        rows = [r for r in joined if r["day"] == day]
        by_day.append({
            "day": day, "evidence": rows[0]["evidence"], "signals": len(rows),
            "decision_counts": {k: sum(r["decision"] == k for r in rows) for k in ("BUY_NOW", "ARM_TOUCH10", "BLOCK")},
            "original": stats([{**r, "pnl": r["original_pnl"]} for r in rows]),
            "gate_spread_le_075": stats([{**r, "pnl": r["gate075_pnl"]} for r in rows]),
            "dre_touch10": stats([{**r, "pnl": r["primary_pnl"]} for r in rows]),
            "dre_rebound5_shadow": stats([{**r, "pnl": r["secondary_pnl"]} for r in rows]),
        })
    def aggregate(evidence, key):
        rows = [r for r in joined if r["evidence"] == evidence]
        return stats([{**r, "pnl": r[key]} for r in rows])
    out = {
        "version": "H09B_DRE_REPLAY_V01", "mode": "RETROSPECTIVE_DIAGNOSTIC_NOT_OOS",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(), "policy": cfg,
        "methodology": [
            "Thresholds were frozen after reviewing data through 2026-10-16; all historical replay is retrospective diagnostic evidence.",
            "ORIGINAL enters at the original H09B ask and marks at the 60m terminal bid.",
            "DRE_TOUCH10 buys immediately only when spread <=0.50%; for 0.50%-0.75% it waits for bid <= -10% vs original ask then enters at contemporaneous ask; spread >0.75% is blocked.",
            "DRE_REBOUND5 is secondary shadow only; first uncontaminated prospective evidence begins after 2026-10-17.",
        ],
        "rows": joined, "by_day": by_day,
        "aggregate": {ev: {
            "original": aggregate(ev, "original_pnl"), "gate_spread_le_075": aggregate(ev, "gate075_pnl"),
            "dre_touch10": aggregate(ev, "primary_pnl"), "dre_rebound5_shadow": aggregate(ev, "secondary_pnl"),
        } for ev in ("DISCOVERY", "PROSPECTIVE")},
    }
    atomic_text(OUT, json.dumps(out, indent=2) + "\n")
    print(json.dumps({"output": str(OUT), "by_day": by_day, "aggregate": out["aggregate"]}, indent=2))


if __name__ == "__main__": main()
