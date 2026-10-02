import json,csv
from options_system.env import load_local_env
from options_system.spy_daily import fetch_daily_spy
from options_system.synthetic_chain import synthetic_chain
from options_system.option_simulator import OptionContract,scenario_pnl
from options_system.empirical_distribution import quantile
load_local_env();rows=fetch_daily_spy("2018-11-01T00:00:00Z","2026-09-01T00:00:00Z");out=[];qs=(.05,.15,.25,.35,.45,.55,.65,.75,.85,.95)
for i,r in enumerate(rows):
 if not ("2024-01-01"<=r["date"]<="2026-08-31") or i+2>=len(rows):continue
 spot=float(r["open"]);dev=[float(rows[j+2]["close"])/float(rows[j]["open"])-1 for j in range(max(0,i-302),i-2)]
 if len(dev)<100:continue
 p=sum(abs(x)>=.01 for x in dev)/len(dev);pc=max(0,p-.05);evs=[x for x in dev if abs(x)>=.01];non=[x for x in dev if abs(x)<.01]
 samples=[(quantile(evs,q),pc/len(qs)) for q in qs]+[(quantile(non,q),(1-pc)/len(qs)) for q in qs]
 best=None
 for x in synthetic_chain(spot,dtes=(3,5,7,10),moneyness=(-.02,-.01,0,.01,.02),iv=.20,spread_pct=.08):
  entry=min(x["ask"],x["mid"]+(x["ask"]-x["bid"])*.25);c=OptionContract(x["option_type"],x["strike"],x["dte"],entry,x["iv"])
  vals=[(scenario_pnl(c,spot*(1+ret),iv=.17,dte=max(0,x["dte"]-3),entry_cost=(entry-x["mid"])*100)["net_pnl"],w) for ret,w in samples]
  ev=sum(v*w for v,w in vals);pp=sum(w for v,w in vals if v>0)
  z={"symbol":x["symbol"],"type":x["option_type"],"dte":x["dte"],"ev":ev,"p_profit":pp}
  if best is None or ev>best["ev"]:best=z
 actual=float(rows[i+2]["close"])/spot-1;out.append({"date":r["date"],"actual_h3":actual,"actual_event":abs(actual)>=.01,**best})
with open("artifacts/o5_walkforward_spy_2024_2026.csv","w",newline="") as f:w=csv.DictWriter(f,fieldnames=out[0]);w.writeheader();w.writerows(out)
pos=[x for x in out if x["ev"]>0];s={"mode":"SIMULATED_OPEN_WALK_FORWARD_FAST_V02","sessions":len(out),"positive_best_ev_sessions":len(pos),"positive_rate":len(pos)/len(out),"best_type_counts":{t:sum(x["type"]==t for x in out) for t in ("call","put")},"positive_type_counts":{t:sum(x["type"]==t and x["ev"]>0 for x in out) for t in ("call","put")},"actual_event_rate":sum(x["actual_event"] for x in out)/len(out),"mean_best_ev":sum(x["ev"] for x in out)/len(out),"note":"20-point conditional quantile approximation; synthetic prices/IV/spreads; diagnostic only."}
open("artifacts/o5_walkforward_spy_2024_2026_summary.json","w").write(json.dumps(s,indent=2));print(json.dumps(s,indent=2))
