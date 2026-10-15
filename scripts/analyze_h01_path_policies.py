#!/usr/bin/env python3
from __future__ import annotations

import bisect
import csv
import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
from statistics import mean, median

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/"artifacts/intraday"
TRACKER=ROOT/"data/processed/intraday/prospective_hypothesis_tracker_v02.csv"
RAW=ROOT/"data/raw/prospective"
OUT=ART/"H01_PATH_POLICY_RESEARCH_V01.json"


def dt(v): return datetime.fromisoformat(str(v).replace("Z","+00:00"))
def num(v):
    try: return float(v)
    except (TypeError,ValueError): return None

def avg(xs):
    x=[v for v in xs if v is not None]; return sum(x)/len(x) if x else None

def med(xs):
    x=[v for v in xs if v is not None]; return median(x) if x else None

rows=list(csv.DictReader(TRACKER.open(encoding="utf-8")))
by_day=defaultdict(list)
for r in rows: by_day[r["decision_date"]].append(r)
for day in by_day: by_day[day].sort(key=lambda r:r["captured_at_utc"])

@lru_cache(maxsize=1024)
def snapshot_for(source_file):
    p=RAW/source_file
    if not p.exists(): return None
    try: return json.loads(p.read_text(encoding="utf-8"))
    except Exception: return None


def contract_bid(source_file, contract):
    d=snapshot_for(source_file)
    try:
        q=d["payload"]["options"]["snapshot"]["snapshots"][contract]["latestQuote"]
        b=num(q.get("bp")); return b if b and b>0 else None
    except Exception: return None


def nearest_row(day, when):
    xs=by_day.get(day) or []; target=dt(when).timestamp(); times=[dt(r["captured_at_utc"]).timestamp() for r in xs]
    i=bisect.bisect_left(times,target); c=[]
    if i<len(xs): c.append((abs(times[i]-target),xs[i]))
    if i: c.append((abs(times[i-1]-target),xs[i-1]))
    return min(c,key=lambda x:x[0])[1] if c else None


def build_path(trade):
    day=trade["decision_date"]; start=dt(trade["entry_time"]); end=start+timedelta(minutes=float(trade.get("horizon_min") or 60))
    contract=trade["contract"]; entry=num(trade["entry_ask"]); start_row=nearest_row(day,trade["signal_time"])
    entry_spot=num(start_row.get("spot")) if start_row else None
    path=[]
    for r in by_day.get(day) or []:
        t=dt(r["captured_at_utc"])
        if t<start: continue
        if t>end: break
        bid=contract_bid(r["source_file"],contract)
        if bid is None or not entry: continue
        path.append({"elapsed_seconds":(t-start).total_seconds(),"bid":bid,"return":bid/entry-1.0,"spot":num(r.get("spot")),"time":r["captured_at_utc"]})
    return entry_spot,path


def evaluate(path, *, tp=.10, sl=.10, grace_seconds=0, confirm_count=1, require_spot_below_entry=False, spot_buffer=0.0, entry_spot=None):
    below_count=0
    for p in path:
        r=p["return"]
        if r>=tp: return {"reason":"TP","return":r,"elapsed_seconds":p["elapsed_seconds"]}
        if p["elapsed_seconds"]<grace_seconds: continue
        stop_ok=r<=-sl
        if require_spot_below_entry and entry_spot and p.get("spot"):
            stop_ok=stop_ok and p["spot"] <= entry_spot*(1.0-spot_buffer)
        if stop_ok: below_count+=1
        else: below_count=0
        if below_count>=confirm_count: return {"reason":"SL","return":r,"elapsed_seconds":p["elapsed_seconds"]}
    if path:
        p=path[-1]; return {"reason":"HORIZON","return":p["return"],"elapsed_seconds":p["elapsed_seconds"]}
    return {"reason":"NO_PATH","return":None,"elapsed_seconds":None}

state=json.loads((ART/"PAPER_TRADING_LIVE_STATE_V01.json").read_text())
trades=[dict(x) for x in state.get("live_ledger",[]) if x.get("hypothesis")=="CALL_FLOW_REVERSAL_V01" and x.get("status")=="CLOSED"]
trades.sort(key=lambda x:x.get("entry_time") or "")

paths=[]
for t in trades:
    entry_spot,path=build_path(t)
    paths.append({"trade":t,"entry_spot":entry_spot,"path":path})

policies={}
for tp in (.10,.15,.20):
    for sl in (.10,.15,.20,.25):
        name=f"TP{int(tp*100)}_SL{int(sl*100)}"
        policies[name]=lambda path,es,tp=tp,sl=sl:evaluate(path,tp=tp,sl=sl,entry_spot=es)
for sec in (60,120,180,300):
    policies[f"TP10_SL10_GRACE_{sec//60}m"]=lambda path,es,sec=sec:evaluate(path,tp=.10,sl=.10,grace_seconds=sec,entry_spot=es)
policies["TP10_SL10_CONFIRM_2_QUOTES"]=lambda path,es:evaluate(path,tp=.10,sl=.10,confirm_count=2,entry_spot=es)
policies["TP10_SL10_SPY_BELOW_ENTRY"]=lambda path,es:evaluate(path,tp=.10,sl=.10,require_spot_below_entry=True,spot_buffer=0.0,entry_spot=es)
policies["TP10_SL10_SPY_BELOW_ENTRY_10BP"]=lambda path,es:evaluate(path,tp=.10,sl=.10,require_spot_below_entry=True,spot_buffer=.001,entry_spot=es)

policy_results={}
for name,fn in policies.items():
    vals=[]; reasons=defaultdict(int); elapsed=[]
    for rec in paths:
        out=fn(rec["path"],rec["entry_spot"]); reasons[out["reason"]]+=1
        if out["return"] is not None: vals.append(out["return"])
        if out["elapsed_seconds"] is not None: elapsed.append(out["elapsed_seconds"])
    policy_results[name]={"n":len(vals),"mean_return":avg(vals),"median_return":med(vals),"win_rate":sum(v>0 for v in vals)/len(vals) if vals else None,
                          "reasons":dict(reasons),"mean_exit_minutes":avg([x/60 for x in elapsed])}

# Winner-vs-loser early path using actual live outcome labels. Historical raw cadence is ~1 minute.
def early_features(rec, seconds):
    pts=[p for p in rec["path"] if p["elapsed_seconds"]<=seconds+20]
    if not pts: return {"last_return":None,"mfe":None,"mae":None,"spot_return":None}
    p=min(pts,key=lambda x:abs(x["elapsed_seconds"]-seconds))
    use=[x for x in rec["path"] if 0<=x["elapsed_seconds"]<=seconds+20]
    entry_spot=rec["entry_spot"]
    return {"last_return":p["return"],"mfe":max((x["return"] for x in use),default=None),"mae":min((x["return"] for x in use),default=None),
            "spot_return":(p["spot"]/entry_spot-1.0) if entry_spot and p.get("spot") else None}

winner_loser={}
for sec in (60,120,180,300):
    grp={"TP10":[],"SL10":[]}
    for rec in paths:
        reason=rec["trade"].get("exit_reason")
        if reason not in grp: continue
        grp[reason].append(early_features(rec,sec))
    winner_loser[f"{sec//60}m"]={}
    for reason,rs in grp.items():
        winner_loser[f"{sec//60}m"][reason]={"n":len(rs),"return_mean":avg([x["last_return"] for x in rs]),"return_median":med([x["last_return"] for x in rs]),
                                                "mfe_mean":avg([x["mfe"] for x in rs]),"mae_mean":avg([x["mae"] for x in rs]),"spot_return_mean":avg([x["spot_return"] for x in rs])}

result={
    "version":"H01_PATH_POLICY_RESEARCH_V01",
    "generated_at_utc":datetime.now(timezone.utc).isoformat(),
    "mode":"COUNTERFACTUAL_RESEARCH_ONLY",
    "scientific_evidence":False,
    "auto_apply":False,
    "frozen_h01_unchanged":True,
    "historical_resolution":"approximately_1_minute",
    "thirty_second_historical_analysis":"UNAVAILABLE_RELIABLY",
    "live_15s_30s_telemetry":"ENABLED_FROM_NEXT_SESSION",
    "trades":len(trades),
    "paths_with_quotes":sum(bool(x["path"]) for x in paths),
    "policy_results":policy_results,
    "winner_vs_loser_early_path":winner_loser,
    "warning":"Grid and structural/temporal stop variants are descriptive counterfactuals. Freeze candidates before prospective validation; do not auto-apply from this sample."
}
OUT.write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps({"output":str(OUT),"trades":len(trades),"paths":result["paths_with_quotes"],"policies":len(policy_results)},indent=2))
