import csv,json
from options_system.env import load_local_env
from options_system.spy_daily import fetch_daily_spy
from options_system.spy_open_features import spy_open_features
from options_system.open_outcomes import open_outcome
from options_system.open_probability_runtime import load_probability_artifact,score_open_features
from options_system.synthetic_chain import synthetic_chain
from options_system.option_simulator import OptionContract,scenario_pnl
from options_system.empirical_distribution import quantile
load_local_env()
rows=fetch_daily_spy("2018-11-01T00:00:00Z","2026-09-01T00:00:00Z")
art=load_probability_artifact("artifacts/o3/O3_OPEN_PATH_H3_PROB_V02.json")
qs=(.05,.15,.25,.35,.45,.55,.65,.75,.85,.95)
def eval_mode(i,mode):
 r=rows[i];feat=spy_open_features(rows,i);prob=score_open_features(art,feat)
 if prob["conservative"]<.80:return None
 dev=[]
 for j in range(max(61,i-302),i-2):
  if j+2<i:dev.append(open_outcome(rows,j,3))
 if len(dev)<100:return None
 rets=[o["terminal_return"] for o in dev]
 if mode=="centered":
  m=sum(rets)/len(rets);rets2=[x-m for x in rets]
 elif mode=="inverted":
  rets2=[-x for x in rets]
 else:rets2=rets
 dev2=[]
 for o,rt in zip(dev,rets2):
  dev2.append({"terminal_return":rt,"mfe":o["mfe"],"mae":o["mae"]})
 evs=[o["terminal_return"] for o in dev2 if max(o["mfe"],-o["mae"])>=.01]
 non=[o["terminal_return"] for o in dev2 if max(o["mfe"],-o["mae"])<.01]
 if len(evs)<10 or len(non)<10:return None
 pc=prob["conservative"];samples=[(quantile(evs,q),pc/len(qs),"EVENT") for q in qs]+[(quantile(non,q),(1-pc)/len(qs),"NON_EVENT") for q in qs]
 spot=float(r["open"]);best={"call":None,"put":None}
 for x in synthetic_chain(spot,dtes=(3,5,7,10),moneyness=(-.02,-.01,0,.01,.02),iv=.20,spread_pct=.08):
  entry=min(x["ask"],x["mid"]+(x["ask"]-x["bid"])*.25);drag=(entry-x["mid"])*100;c=OptionContract(x["option_type"],x["strike"],x["dte"],entry,x["iv"])
  def ev_at(iv):
   ev=0;pp=0
   for ret,w,g in samples:
    pnl=scenario_pnl(c,spot*(1+ret),iv=iv,dte=max(0,x["dte"]-3),entry_cost=drag/2,exit_cost=drag/2)["net_pnl"];ev+=pnl*w;pp+=w if pnl>0 else 0
   return ev,pp
  ev,pp=ev_at(.20);stress=[ev_at(v)[0] for v in (.17,.20,.23)];robust=ev>0 and all(v>0 for v in stress)
  z={"symbol":x["symbol"],"type":x["option_type"],"ev":ev,"p_profit":pp,"robust":robust}
  if robust and (best[x["option_type"]] is None or ev>best[x["option_type"]]["ev"]):best[x["option_type"]]=z
 return {"date":r["date"],"p_conservative":pc,"best_call":best["call"],"best_put":best["put"]}
modes={m:[] for m in ("original","centered","inverted")}
for i,r in enumerate(rows):
 if not ("2024-01-01"<=r["date"]<="2026-08-31") or i+2>=len(rows):continue
 for m in modes:
  z=eval_mode(i,m)
  if z:modes[m].append(z)
summary={}
for m,arr in modes.items():
 calls=[x for x in arr if x["best_call"]];puts=[x for x in arr if x["best_put"]]
 both=[x for x in arr if x["best_call"] and x["best_put"]]
 summary[m]={"gated_sessions":len(arr),"robust_call_sessions":len(calls),"robust_put_sessions":len(puts),"both":len(both),
 "mean_call_ev":sum(x["best_call"]["ev"] for x in calls)/len(calls) if calls else None,
 "mean_put_ev":sum(x["best_put"]["ev"] for x in puts)/len(puts) if puts else None}
open("artifacts/o5_drift_counterfactual_walkforward_v04.json","w").write(json.dumps(summary,indent=2))
with open("artifacts/o5_drift_counterfactual_walkforward_v04.csv","w",newline="") as f:
 fields=["mode","date","p_conservative","call_ev","put_ev","call_symbol","put_symbol"];w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
 for m,arr in modes.items():
  for x in arr:w.writerow({"mode":m,"date":x["date"],"p_conservative":x["p_conservative"],"call_ev":x["best_call"]["ev"] if x["best_call"] else None,"put_ev":x["best_put"]["ev"] if x["best_put"] else None,"call_symbol":x["best_call"]["symbol"] if x["best_call"] else None,"put_symbol":x["best_put"]["symbol"] if x["best_put"] else None})
print(json.dumps(summary,indent=2))
