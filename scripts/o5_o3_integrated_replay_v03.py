import json
from options_system.env import load_local_env
from options_system.spy_daily import fetch_daily_spy
from options_system.spy_open_features import spy_open_features
from options_system.open_outcomes import open_outcome
from options_system.open_probability_runtime import load_probability_artifact,score_open_features
from options_system.synthetic_chain import synthetic_chain
from options_system.simulation_lab_path import evaluate_synthetic_chain_path
load_local_env();rows=fetch_daily_spy("2018-11-01T00:00:00Z","2026-09-01T00:00:00Z")
date="2024-06-03";i=next(i for i,r in enumerate(rows) if r["date"]==date);spot=float(rows[i]["open"])
feat=spy_open_features(rows,i);art=load_probability_artifact("artifacts/o3/O3_OPEN_PATH_H3_PROB_V02.json");prob=score_open_features(art,feat)
dev=[]
for j in range(61,i):
 if j+2<i:
  o=open_outcome(rows,j,3);dev.append({"terminal_return":o["terminal_return"],"mfe":o["mfe"],"mae":o["mae"]})
chain=synthetic_chain(spot,dtes=(3,5,7,10),moneyness=(-.02,-.01,0,.01,.02),iv=.20,spread_pct=.08)
cards=evaluate_synthetic_chain_path(chain,spot,dev,prob["raw"],prob["calibrated"],prob["conservative"])
cards=sorted(cards,key=lambda x:x["ev"]["conservative"]["expected_pnl"],reverse=True)
actual=open_outcome(rows,i,3);actual_event=max(actual["mfe"],-actual["mae"])>=.01
out={"mode":"SIMULATED_OPEN_CAUSAL_REPLAY_O3_TO_O5_V03","decision_date":date,"spot_open":spot,"development_n":len(dev),
"probability":prob,"actual_revealed_after_decision":{"path_event_1pct_h3":actual_event,"terminal_return":actual["terminal_return"],"mfe":actual["mfe"],"mae":actual["mae"]},
"top5":[{"symbol":x["symbol"],"type":x["option_type"],"strike":x["strike"],"dte":x["dte"],"entry_fill":x["entry_fill"],
"ev_raw":x["ev"]["raw"]["expected_pnl"],"ev_calibrated":x["ev"]["calibrated"]["expected_pnl"],"ev_conservative":x["ev"]["conservative"]["expected_pnl"],
"p_profit_conservative":x["ev"]["conservative"]["p_profit"],"robust_positive_count":x["robust_positive_count"],"stress_count":x["stress_count"]} for x in cards[:5]],
"note":"Synthetic contracts/IV/spreads; diagnostic research only. O3 predicts path excursion magnitude, not direction."}
open("artifacts/o5_o3_integrated_replay_2024-06-03_v03.json","w").write(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
