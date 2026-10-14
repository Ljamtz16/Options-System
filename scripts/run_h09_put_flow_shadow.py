#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path

from options_system.h09_put_flow import candidate_active, is_new_episode, summarize

ROOT = Path(__file__).resolve().parents[1]
CFG = ROOT / "config/h09_put_flow_shadow_v01.json"
TRACKER = ROOT / "data/processed/intraday/prospective_hypothesis_tracker_v02.csv"
OUT = ROOT / "artifacts/intraday/H09_PUT_FLOW_PROSPECTIVE_V01.json"

cfg = json.loads(CFG.read_text(encoding="utf-8"))
rows = list(csv.DictReader(TRACKER.open(encoding="utf-8")))
rows.sort(key=lambda x: x.get("captured_at_utc", ""))
last = {}
episodes = []
for row in rows:
    day = row.get("decision_date") or ""
    for cand in cfg["candidates"]:
        if not candidate_active(cand, row):
            continue
        key = f"{day}|{cand['id']}"
        if not is_new_episode(last.get(key), row["captured_at_utc"], cfg["episode_gap_minutes"]):
            continue
        last[key] = row["captured_at_utc"]
        rec = dict(row)
        rec["candidate_id"] = cand["id"]
        rec["evidence_partition"] = "DISCOVERY" if day <= cfg["discovery_cutoff"] else "PROSPECTIVE"
        episodes.append(rec)

def partition(name):
    part = [x for x in episodes if x["evidence_partition"] == name]
    return {
        "episodes": len(part),
        "by_candidate": {c["id"]: summarize(part, c["id"], cfg["evaluation_horizons_minutes"]) for c in cfg["candidates"]},
        "rows": part,
    }

result = {
    "version": cfg["version"],
    "mode": cfg["mode"],
    "discovery_cutoff": cfg["discovery_cutoff"],
    "prospective_start_after": cfg["prospective_start_after"],
    "scientific_evidence": False,
    "frozen_h01_unchanged": True,
    "discovery": partition("DISCOVERY"),
    "prospective": partition("PROSPECTIVE"),
}
OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps({
    "version": result["version"],
    "discovery_episodes": result["discovery"]["episodes"],
    "prospective_episodes": result["prospective"]["episodes"],
    "output": str(OUT),
}, indent=2))
