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
qs=(.05,.15,.25,.35,.45,.55,.65,.75,.85,.95);out=[]
for i,r in enumerate(rows):
 if not ("2024-01-01"<=r["date"]<="2026-08-31") or i+2>=len(rows):continue
 feat=spy_open_features(rows,i)
 if not feat:continue
 prob=score_open_features(art,feat);gate=prob["conservative"]>=.80
 actual=open_outcome(rows,i,3);actual_event=max(actual["mfe"],-actual["mae"])>=.01
 rec={"date":r["date"],"p_raw":prob["raw"],"p_calibrated":prob["calibrated"],"p_conservative":prob["conservative"],"activity_pass":gate,"actual_event":actual_event,
 "actual_terminal":actual["terminal_return"],"best_type":None,"best_symbol":None,"best_ev":None,"best_p_profit":None,"robust_survivors":0,"positive_ev_contracts":0}
 if gate:
  dev=[]
  for j in range(max(61,i-302),i-2):
   if j+2<i:
    o=open_outcome(rows,j,3);dev.append(o)
  evs=[o["terminal_return"] for o in dev if max(o["mfe"],-o["mae"])>=.01]
  non=[o["terminal_return"] for o in dev if max(o["mfe"],-o["mae"])<.01]
  if len(evs)>=10 and len(non)>=10:
   pc=prob["conservative"];samples=[(quantile(evs,q),pc/len(qs),"EVENT") for q in qs]+[(quantile(non,q),(1-pc)/len(qs),"NON_EVENT") for q in qs]
   spot=float(r["open"]);best=None
   for x in synthetic_chain(spot,dtes=(3,5,7,10),moneyness=(-.02,-.01,0,.01,.02),iv=.20,spread_pct=.08):
    entry=min(x["ask"],x["mid"]+(x["ask"]-x["bid"])*.25);drag=(entry-x["mid"])*100;c=OptionContract(x["option_type"],x["strike"],x["dte"],entry,x["iv"])
    def ev_at(iv):
     vals=[]
     for ret,w,g in samples:
      pnl=scenario_pnl(c,spot*(1+ret),iv=iv,dte=max(0,x["dte"]-3),entry_cost=drag/2,exit_cost=drag/2)["net_pnl"];vals.append((pnl,w))
     return sum(v*w for v,w in vals),sum(w for v,w in vals if v>0)
    ev,pp=ev_at(.20);stress=[ev_at(v)[0] for v in (.17,.20,.23)]
    if ev>0:rec["positive_ev_contracts"]+=1
    robust=ev>0 and all(v>0 for v in stress)
    if robust:rec["robust_survivors"]+=1
    z={"symbol":x["symbol"],"type":x["option_type"],"ev":ev,"p_profit":pp,"robust":robust}
    if robust and (best is None or ev>best["ev"]):best=z
   if best:rec.update({"best_type":best["type"],"best_symbol":best["symbol"],"best_ev":best["ev"],"best_p_profit":best["p_profit"]})
 out.append(rec)
with open("artifacts/o5_o3_walkforward_2024_2026_v03.csv","w",newline="") as f:w=csv.DictWriter(f,fieldnames=out[0]);w.writeheader();w.writerows(out)
passes=[x for x in out if x["activity_pass"]];surv=[x for x in passes if x["best_symbol"]];summary={
 "mode":"O3_TO_O5_OPEN_WALKFORWARD_V03_DIAGNOSTIC","sessions":len(out),"activity_pass_sessions":len(passes),"activity_pass_rate":len(passes)/len(out),
 "activity_pass_event_rate":sum(x["actual_event"] for x in passes)/len(passes) if passes else None,
 "sessions_with_robust_contract":len(surv),"robust_session_rate_all":len(surv)/len(out),"robust_session_rate_after_gate":len(surv)/len(passes) if passes else None,
 "best_type_counts":{t:sum(x["best_type"]==t for x in surv) for t in ("call","put")},"positive_ev_contracts_total":sum(x["positive_ev_contracts"] for x in passes),
 "robust_contracts_total":sum(x["robust_survivors"] for x in passes),"mean_best_ev":sum(x["best_ev"] for x in surv)/len(surv) if surv else None,
 "old_reference":{"positive_best_ev_sessions":219,"positive_type_counts":{"call":219,"put":0}},
 "note":"2024-2026 already inspected diagnostic only. Frozen O3 model/calibration; no refit. Synthetic contracts/IV/spreads; 20-point path-bucket terminal-return approximation."}
open("artifacts/o5_o3_walkforward_2024_2026_v03_summary.json","w").write(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
