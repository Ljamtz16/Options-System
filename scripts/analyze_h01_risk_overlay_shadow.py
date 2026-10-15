#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/"artifacts/intraday"
CFG=ROOT/"config/h01_risk_overlay_shadow_v01.json"
HEALTH=ART/"STRATEGY_HEALTH_GATE_SHADOW_V01.json"
OUT=ART/"H01_RISK_OVERLAY_SHADOW_V01.json"


def num(v):
    try:return float(v)
    except (TypeError,ValueError):return None


def summarize(rows):
    vals=[num(r.get("pnl")) for r in rows]; vals=[x for x in vals if x is not None]
    return {"n":len(rows),"net_pnl":sum(vals) if vals else 0.0,"mean_pnl":mean(vals) if vals else None,
            "win_rate":sum(x>0 for x in vals)/len(vals) if vals else None}

cfg=json.loads(CFG.read_text())
health=json.loads(HEALTH.read_text())
base_rows=(health.get("candidates") or {}).get("SHG02_CORE_VIX",{}).get("rows") or []
result={"version":cfg["version"],"mode":cfg["mode"],"generated_at_utc":datetime.now(timezone.utc).isoformat(),
        "discovery_cutoff":cfg["discovery_cutoff"],"prospective_start_after":cfg["prospective_start_after"],
        "scientific_evidence":False,"auto_apply":False,"broker_orders_enabled":False,"candidates":{}}
for cand in cfg["candidates"]:
    selected=[]; last_by_day={}
    for r in sorted(base_rows,key=lambda x:(x.get("day") or "",x.get("time") or "")):
        if cand.get("health_gate") and r.get("decision")!="ALLOW":
            continue
        t=datetime.fromisoformat(str(r["time"]).replace("Z","+00:00")); day=r["day"]
        cd=int(cand.get("cooldown_minutes") or 0)
        last=last_by_day.get(day)
        if last is not None and (t-last).total_seconds()<cd*60:
            continue
        selected.append({**r,"partition":"DISCOVERY" if day<=cfg["discovery_cutoff"] else "PROSPECTIVE"})
        last_by_day[day]=t
    parts={}
    for part in ("DISCOVERY","PROSPECTIVE"):
        xs=[x for x in selected if x["partition"]==part]
        parts[part]={"summary":summarize(xs),"by_day":{}}
        for day in sorted(set(x["day"] for x in xs)):
            parts[part]["by_day"][day]=summarize([x for x in xs if x["day"]==day])
    result["candidates"][cand["id"]]={"health_gate":cand.get("health_gate"),"cooldown_minutes":cand.get("cooldown_minutes"),"partitions":parts}
result["comparators"]=cfg.get("comparators")
result["warning"]="Discovery performance selected these candidates. Do not promote until later sessions provide prospective evidence."
OUT.write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps({"output":str(OUT),"candidates":len(cfg["candidates"])},indent=2))
