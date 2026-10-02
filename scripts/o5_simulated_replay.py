import json
from options_system.env import load_local_env
from options_system.spy_daily import fetch_daily_spy
from options_system.synthetic_chain import synthetic_chain
from options_system.simulation_lab import evaluate_synthetic_chain
load_local_env();rows=fetch_daily_spy("2018-11-01T00:00:00Z","2026-09-01T00:00:00Z")
date="2024-06-03";i=next(i for i,r in enumerate(rows) if r["date"]==date);spot=float(rows[i]["close"])
dev=[]
for j in range(0,i-3):
 if rows[j]["date"]<date:dev.append(float(rows[j+3]["close"])/float(rows[j]["close"])-1)
actual=float(rows[i+3]["close"])/spot-1
# Simulation-only probability: expanding-history empirical event frequency. Not O3 production probability.
p=sum(abs(x)>=.01 for x in dev)/len(dev);pcons=max(0,p-.05)
chain=synthetic_chain(spot,dtes=(3,5,7,10),moneyness=(-.02,-.01,0,.01,.02),iv=.20,spread_pct=.08)
cards=evaluate_synthetic_chain(chain,spot,dev,p,p,pcons)
cards=sorted(cards,key=lambda x:x["ev"]["conservative"]["expected_pnl"],reverse=True)
summary={"mode":"SIMULATED_REPLAY","decision_date":date,"spot_reference_close":spot,"development_n":len(dev),
 "simulation_probability_method":"expanding historical event frequency; NOT O3 production model","p_event":p,"p_conservative":pcons,
 "actual_h3_return_revealed_after_evaluation":actual,"top5":[{"symbol":x["symbol"],"type":x["option_type"],"strike":x["strike"],"dte":x["dte"],"entry_fill":x["entry_fill"],"ev_conservative":x["ev"]["conservative"]["expected_pnl"],"p_profit_conservative":x["ev"]["conservative"]["p_profit"],"robust":f'{x["robust_positive_count"]}/{x["stress_count"]}',"worst_stress_ev":x["worst_stress_ev"]} for x in cards[:5]]}
open("artifacts/o5_simulated_replay_2024-06-03.json","w").write(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
