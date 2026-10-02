import csv,json,os
from options_system.env import load_local_env
from options_system.spy_daily import fetch_daily_spy
from options_system.spy_open_features import spy_open_features,FEATURE_NAMES
from options_system.open_outcomes import open_outcomes
load_local_env();r=fetch_daily_spy("2018-11-01T00:00:00Z","2026-09-01T00:00:00Z");out=[]
for i in range(len(r)):
 f=spy_open_features(r,i)
 if not f:continue
 o=open_outcomes(r,i)
 row={k:f[k] for k in ["decision_date","decision_time","feature_asof_date","open_t"]+FEATURE_NAMES}
 for h,x in o.items():
  row[f"terminal_h{h}"]=None if x is None else x["terminal_return"];row[f"mfe_h{h}"]=None if x is None else x["mfe"];row[f"mae_h{h}"]=None if x is None else x["mae"];row[f"label_end_h{h}"]=None if x is None else x["label_end"]
 out.append(row)
os.makedirs("data/processed/o2_open",exist_ok=True)
with open("data/processed/o2_open/spy_open_outcomes_v02.csv","w",newline="") as f:w=csv.DictWriter(f,fieldnames=out[0]);w.writeheader();w.writerows(out)
s={"rows":len(out),"first":out[0]["decision_date"],"last":out[-1]["decision_date"],"features":FEATURE_NAMES,"decision_time":"OPEN","status":"CAUSAL_DATASET_V02"}
open("artifacts/o2_open_dataset_v02_summary.json","w").write(json.dumps(s,indent=2));print(json.dumps(s,indent=2))
