import csv,json
from options_system.env import load_local_env
from options_system.spy_daily import fetch_daily_spy
from options_system.spy_open_features import spy_open_features
from options_system.open_outcomes import open_outcome
from options_system.open_probability_runtime import load_probability_artifact,score_open_features
from options_system.synthetic_chain import synthetic_chain
from options_system.option_simulator import OptionContract,scenario_pnl
from options_system.empirical_distribution import quantile
load_local_env();rows=fetch_daily_spy("2018-11-01T00:00:00Z","2026-09-01T00:00:00Z");art=load_probability_artifact("artifacts/o3/O3_OPEN_PATH_H3_PROB_V02.json");qs=(.1,.3,.5,.7,.9)
thresholds=(.50,.55,.60,.65,.70,.75)
summary={str(t):{"gated":0,"robust_put_sessions":0,"robust_call_sessions":0} for t in thresholds}
for i,r in enumerate(rows):
 if not ("2024-01-01"<=r["date"]<="2026-08-31") or i+2>=len(rows):continue
 prob=score_open_features(art,spy_open_features(rows,i))
 if prob["conservative"]<.80:continue
 dev=[open_outcome(rows,j,3) for j in range(max(61,i-302),i-2) if j+2<i]
 rets=[o["terminal_return"] for o in dev];m=sum(rets)/len(rets);center=[x-m for x in rets]
 pos=[x for x in center if x>0];neg=[x for x in center if x<0];zero=[x for x in center if x==0]
 if len(pos)<5 or len(neg)<5:continue
 spot=float(r["open"])
 for pd in thresholds:
  summary[str(pd)]["gated"]+=1
  pu=1-pd
  samples=[(quantile(pos,q),pu/len(qs),"UP") for q in qs]+[(quantile(neg,q),pd/len(qs),"DOWN") for q in qs]
  best={"call":False,"put":False}
  for x in synthetic_chain(spot,dtes=(3,5,7,10),moneyness=(-.02,-.01,0,.01,.02),iv=.20,spread_pct=.08):
   entry=min(x["ask"],x["mid"]+(x["ask"]-x["bid"])*.25);drag=(entry-x["mid"])*100;c=OptionContract(x["option_type"],x["strike"],x["dte"],entry,x["iv"])
   vals=[]
   robust=True
   for iv in (.17,.20,.23):
    ev=0
    for ret,w,g in samples:
     pnl=scenario_pnl(c,spot*(1+ret),iv=iv,dte=max(0,x["dte"]-3),entry_cost=drag/2,exit_cost=drag/2)["net_pnl"];ev+=pnl*w
    vals.append(ev)
   if all(v>0 for v in vals):best[x["option_type"]]=True
  if best["call"]:summary[str(pd)]["robust_call_sessions"]+=1
  if best["put"]:summary[str(pd)]["robust_put_sessions"]+=1
open("artifacts/o5_directional_sensitivity_put_v04.json","w").write(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
