import json,statistics,csv
from pathlib import Path
from datetime import datetime,date,timedelta
from options_system.intraday_contracts import representative_contracts,conservative_long_pnl

ROOT=Path("data/raw/prospective")
DAY="2026-10-02"
HORIZONS=(15,30,60)

def load_rows():
 rows=[]
 for f in sorted(ROOT.glob("spy_options_*.json")):
  obj=json.loads(f.read_text(encoding="utf-8"));p=obj["payload"]
  rs=p.get("research_state") or {}
  if (rs.get("features") or {}).get("decision_date")!=DAY:continue
  u=p["underlying"]["snapshot"];t=u.get("latestTrade") or {};q=u.get("latestQuote") or {}
  spot=t.get("p") or (((q.get("bp") or 0)+(q.get("ap") or 0))/2 or None)
  rows.append({"ts":datetime.fromisoformat(obj["captured_at_utc"]),"spot":float(spot),
               "chain":p["options"]["snapshot"],"file":f.name})
 return sorted(rows,key=lambda x:x["ts"])

def future(rows,i,minutes):
 target=rows[i]["ts"]+timedelta(minutes=minutes)
 xs=[r for r in rows[i+1:] if target<=r["ts"]<=target+timedelta(minutes=6)]
 return xs[0] if xs else None
def summarize(xs):
 xs=[x for x in xs if x is not None]
 if not xs:return {"n":0}
 return {"n":len(xs),"mean":sum(xs)/len(xs),"median":statistics.median(xs),
         "win_rate":sum(x>0 for x in xs)/len(xs),
         "gt10_rate":sum(x>=.10 for x in xs)/len(xs),
         "best":max(xs),"worst":min(xs)}

def main():
 rows=load_rows();out=[];md=date.fromisoformat(DAY)
 for i,r in enumerate(rows):
  reps=representative_contracts(r["chain"],md)
  rec={"captured_at_utc":r["ts"].isoformat(),"spot":r["spot"],
       "call":(reps.get("call") or {}).get("symbol"),"put":(reps.get("put") or {}).get("symbol")}
  for h in HORIZONS:
   f=future(rows,i,h)
   if not f:continue
   rec[f"spy_ret_{h}m"]=f["spot"]/r["spot"]-1
   for side in ("call","put"):
    pnl=conservative_long_pnl(reps.get(side),f["chain"])
    rec[f"{side}_ret_{h}m"]=pnl["return"] if pnl else None
  if i<len(rows)-1:
   eod=rows[-1];rec["spy_ret_eod"]=eod["spot"]/r["spot"]-1
   for side in ("call","put"):
    pnl=conservative_long_pnl(reps.get(side),eod["chain"])
    rec[f"{side}_ret_eod"]=pnl["return"] if pnl else None
  out.append(rec)
 summary={"day":DAY,"snapshots":len(rows),"first_utc":rows[0]["ts"].isoformat() if rows else None,
          "last_utc":rows[-1]["ts"].isoformat() if rows else None,"horizons":{}}
 for h in HORIZONS:
  summary["horizons"][str(h)]={
   "spy":summarize([r.get(f"spy_ret_{h}m") for r in out]),
   "call":summarize([r.get(f"call_ret_{h}m") for r in out]),
   "put":summarize([r.get(f"put_ret_{h}m") for r in out])}
 summary["eod"]={"spy":summarize([r.get("spy_ret_eod") for r in out]),
                 "call":summarize([r.get("call_ret_eod") for r in out]),
                 "put":summarize([r.get("put_ret_eod") for r in out])}
 Path("artifacts/intraday").mkdir(parents=True,exist_ok=True)
 Path("artifacts/intraday/SPY_2026-10-02_BOOTSTRAP.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
 fields=sorted({k for r in out for k in r})
 with open("artifacts/intraday/SPY_2026-10-02_BOOTSTRAP.csv","w",newline="",encoding="utf-8") as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(out)
 print(json.dumps(summary))

if __name__=="__main__":main()
