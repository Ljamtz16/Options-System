#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/"artifacts/intraday"
CFG=ROOT/"config/strategy_health_gate_v01.json"
SRC=ART/"SYSTEM_RESEARCH_DIAGNOSTICS_V01.json"
OUT=ART/"STRATEGY_HEALTH_GATE_SHADOW_V01.json"


def num(v):
    try:return float(v)
    except (TypeError,ValueError):return None


def summarize(rows):
    vals=[num(r.get("pnl")) for r in rows]; vals=[x for x in vals if x is not None]
    return {"n":len(rows),"net_pnl":sum(vals) if vals else 0.0,"mean_pnl":mean(vals) if vals else None,
            "win_rate":sum(x>0 for x in vals)/len(vals) if vals else None}

cfg=json.loads(CFG.read_text())
src=json.loads(SRC.read_text())
rows=(src.get("h01") or {}).get("health_rows") or []
result={"version":cfg["version"],"mode":cfg["mode"],"generated_at_utc":datetime.now(timezone.utc).isoformat(),
        "discovery_cutoff":cfg["discovery_cutoff"],"prospective_start_after":cfg["prospective_start_after"],
        "scientific_evidence":False,"auto_apply":False,"broker_orders_enabled":False,"candidates":{}}
for cand in cfg["candidates"]:
    cid=cand["id"]; blocked=[]; allowed=[]; labeled=[]
    for r in rows:
        flags=set(r.get("flags") or []); hits=sorted(flags.intersection(cand["block_if_any"])); is_blocked=bool(hits)
        rec={**r,"health_gate":cid,"decision":"BLOCK" if is_blocked else "ALLOW","triggered":hits,
             "partition":"DISCOVERY" if str(r.get("day"))<=cfg["discovery_cutoff"] else "PROSPECTIVE"}
        labeled.append(rec); (blocked if is_blocked else allowed).append(rec)
    parts={}
    for part in ("DISCOVERY","PROSPECTIVE"):
        pr=[x for x in labeled if x["partition"]==part]
        pa=[x for x in pr if x["decision"]=="ALLOW"]; pb=[x for x in pr if x["decision"]=="BLOCK"]
        parts[part]={"all":summarize(pr),"allowed":summarize(pa),"blocked_counterfactual":summarize(pb),"blocked_rate":len(pb)/len(pr) if pr else None}
    result["candidates"][cid]={"block_if_any":cand["block_if_any"],"partitions":parts,"rows":labeled}
result["monitor_only_flags"]=cfg["monitor_only_flags"]
result["warning"]="Candidates were frozen after inspecting data through 2026-10-15. Only sessions after that date are prospective evidence. No live trade is blocked."
OUT.write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps({"output":str(OUT),"rows":len(rows),"candidates":len(cfg["candidates"])},indent=2))
