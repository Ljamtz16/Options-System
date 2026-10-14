#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

from options_system.multisymbol_shadow import derive_row, active_candidates, is_new_episode, summarize_episodes, signal_key

ROOT = Path(__file__).resolve().parents[1]
CFG = ROOT / "config/multisymbol_shadow_v01.json"
DATA = ROOT / "data/processed/intraday/intraday_options_v2.csv"
OUT = ROOT / "artifacts/intraday/MULTISYMBOL_DISCOVERY_V01.json"
PROSPECTIVE = ROOT / "artifacts/intraday/MULTISYMBOL_PROSPECTIVE_V01.json"

cfg = json.loads(CFG.read_text(encoding="utf-8"))
raw = list(csv.DictReader(DATA.open(encoding="utf-8")))
groups = defaultdict(list)
for row in raw:
    if row.get("symbol") in cfg["symbols"]:
        groups[(row["market_date"], row["symbol"])].append(row)

market_first_by_day = defaultdict(dict)
for (day, symbol), items in groups.items():
    if symbol in {"SPY", "QQQ", "IWM"} and items:
        first = min(items, key=lambda x: x["captured_at_utc"])
        market_first_by_day[day][symbol] = float(first["spot"])

episodes = []
for (day, symbol), rows in sorted(groups.items()):
    rows.sort(key=lambda x: x["captured_at_utc"])
    first_spot = float(rows[0]["spot"]) if rows and rows[0].get("spot") else None
    history = []
    last = {}
    for base in rows:
        row = derive_row(base, first_spot, history, market_first_by_day.get(day))
        for cand in active_candidates(cfg, row):
            key = signal_key(cand["id"], symbol)
            if not is_new_episode(last.get(key), row["captured_at_utc"], cfg["episode_gap_minutes"]):
                continue
            last[key] = row["captured_at_utc"]
            rec = dict(row)
            rec["candidate_id"] = cand["id"]
            rec["candidate_side"] = cand["side"]
            rec["evidence_partition"] = "DISCOVERY" if day <= cfg["discovery_cutoff"] else "PROSPECTIVE"
            episodes.append(rec)
        history.append({"captured_at_utc": row["captured_at_utc"], "spot": row["spot"]})
        history = history[-8:]

def summarize_partition(rows):
    by_candidate = {}
    by_symbol = {}
    for cand in cfg["candidates"]:
        cid = cand["id"]
        by_candidate[cid] = summarize_episodes(rows, cand, cfg["evaluation_horizons_minutes"])
        by_symbol[cid] = {}
        for symbol in cfg["symbols"]:
            subset = [r for r in rows if r.get("symbol") == symbol]
            by_symbol[cid][symbol] = summarize_episodes(subset, cand, cfg["evaluation_horizons_minutes"])
    return {"episodes": len(rows), "by_candidate": by_candidate, "by_candidate_symbol": by_symbol}

discovery_rows = [r for r in episodes if r["evidence_partition"] == "DISCOVERY"]
prospective_rows = [r for r in episodes if r["evidence_partition"] == "PROSPECTIVE"]
report = {
    "version": cfg["version"],
    "mode": cfg["mode"],
    "discovery_cutoff": cfg["discovery_cutoff"],
    "prospective_start_after": cfg["prospective_start_after"],
    "scientific_evidence": False,
    "selection_policy": "PRESPECIFIED_FAMILIES_NO_GRID_OPTIMIZATION",
    "candidates": cfg["candidates"],
    "discovery": summarize_partition(discovery_rows),
}
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
prospective = {
    "version": cfg["version"],
    "mode": cfg["mode"],
    "prospective_start_after": cfg["prospective_start_after"],
    "scientific_evidence": False,
    "summary": summarize_partition(prospective_rows),
    "rows": prospective_rows,
}
PROSPECTIVE.write_text(json.dumps(prospective, indent=2), encoding="utf-8")
print(json.dumps({
    "version": cfg["version"],
    "rows": len(raw),
    "discovery_episodes": len(discovery_rows),
    "prospective_episodes": len(prospective_rows),
    "output": str(OUT),
}, indent=2))
