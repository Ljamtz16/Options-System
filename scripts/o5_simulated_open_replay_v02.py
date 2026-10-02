import json
from options_system.env import load_local_env
from options_system.spy_daily import fetch_daily_spy
from options_system.synthetic_chain import synthetic_chain
from options_system.simulation_lab import evaluate_synthetic_chain
load_local_env();rows=fetch_daily_spy("2018-11-01T00:00:00Z","2026-09-01T00:00:00Z")
date="2024-06-03";i=next(i for i,r in enumerate(rows) if r["date"]==date);spot=float(rows[i]["open"])
dev=[]
for j in range(0,i):
 if j+2<i:
  anchor=float(rows[j]["open"]);ret=float(rows[j+2]["close"])/anchor-1;dev.append(ret)
# H3 OPEN horizon = sessions t,t+1,t+2, terminal close at t+2
actual=float(rows[i+2]["close"])/spot-1
p=sum(abs(x)>=.01 for x in dev)/len(dev);pcons=max(0,p-.05)
chain=synthetic_chain(spot,dtes=(3,5,7,10),moneyness=(-.02,-.01,0,.01,.02),iv=.20,spread_pct=.08)
cards=evaluate_synthetic_chain(chain,spot,dev,p,p,pcons);cards=sorted(cards,key=lambda x:x["ev"]["conservative"]["expected_pnl"],reverse=True)
summary={"mode":"SIMULATED_OPEN_CAUSAL_REPLAY_V02","decision_date":date,"decision_time":"OPEN","spot_reference_open":spot,
"development_n":len(dev),"probability_method":"expanding pre-decision historical event frequency; simulation baseline, NOT O3 production model",
"p_event":p,"p_conservative":pcons,"actual_h3_terminal_return_revealed_after_evaluation":actual,
"top5":[{"symbol":x["symbol"],"type":x["option_type"],"strike":x["strike"],"dte":x["dte"],"entry_fill":x["entry_fill"],"ev_conservative":x["ev"]["conservative"]["expected_pnl"],"p_profit_conservative":x["ev"]["conservative"]["p_profit"],"robust_positive_count":x["robust_positive_count"],"stress_count":x["stress_count"],"worst_stress_ev":x["worst_stress_ev"]} for x in cards[:5]]}
open("artifacts/o5_simulated_open_replay_2024-06-03_v02.json","w").write(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
