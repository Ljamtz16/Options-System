import json,csv
from options_system.env import load_local_env
from options_system.spy_daily import fetch_daily_spy
from options_system.synthetic_chain import synthetic_chain
from options_system.simulation_lab import evaluate_synthetic_chain
load_local_env();rows=fetch_daily_spy("2018-11-01T00:00:00Z","2026-09-01T00:00:00Z")
out=[]
for i,r in enumerate(rows):
 if not ("2024-01-01"<=r["date"]<="2026-08-31") or i+2>=len(rows):continue
 spot=float(r["open"]);dev=[float(rows[j+2]["close"])/float(rows[j]["open"])-1 for j in range(i-2)]
 if len(dev)<100:continue
 # deterministic capped development window keeps replay tractable and causal
 sample=dev[-300:];p=sum(abs(x)>=.01 for x in sample)/len(sample);pc=max(0,p-.05)
 chain=synthetic_chain(spot,dtes=(3,5,7,10),moneyness=(-.02,-.01,0,.01,.02),iv=.20,spread_pct=.08)
 cards=evaluate_synthetic_chain(chain,spot,sample,p,p,pc);cards.sort(key=lambda x:x["ev"]["conservative"]["expected_pnl"],reverse=True);b=cards[0]
 actual=float(rows[i+2]["close"])/spot-1
 out.append({"date":r["date"],"actual_h3":actual,"actual_event":abs(actual)>=.01,"best_symbol":b["symbol"],"best_type":b["option_type"],"best_dte":b["dte"],"best_ev_cons":b["ev"]["conservative"]["expected_pnl"],"best_p_profit":b["ev"]["conservative"]["p_profit"],"robust_positive":b["robust_positive_count"],"worst_stress_ev":b["worst_stress_ev"]})
p="artifacts/o5_walkforward_spy_2024_2026.csv"
with open(p,"w",newline="") as f:w=csv.DictWriter(f,fieldnames=out[0].keys());w.writeheader();w.writerows(out)
pos=[x for x in out if x["best_ev_cons"]>0];rob=[x for x in pos if x["robust_positive"]==9 and x["worst_stress_ev"]>0]
s={"mode":"SIMULATED_OPEN_WALK_FORWARD","development_window":300,"sessions":len(out),"positive_best_ev_sessions":len(pos),"positive_rate":len(pos)/len(out),"fully_robust_positive_sessions":len(rob),"fully_robust_rate":len(rob)/len(out),"best_type_counts":{t:sum(x["best_type"]==t for x in out) for t in ("call","put")},"positive_type_counts":{t:sum(x["best_type"]==t and x["best_ev_cons"]>0 for x in out) for t in ("call","put")},"actual_event_rate":sum(x["actual_event"] for x in out)/len(out),"mean_best_ev":sum(x["best_ev_cons"] for x in out)/len(out),"important":"Synthetic option prices/IV/spreads; diagnostic only."}
open("artifacts/o5_walkforward_spy_2024_2026_summary.json","w").write(json.dumps(s,indent=2));print(json.dumps(s,indent=2))
