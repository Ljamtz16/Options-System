import json,hashlib
from pathlib import Path
src=json.load(open("artifacts/o2/o2_stability_v01.json"))
contract={"id":"O2-H3-MAGNITUDE-V01","status":"FROZEN_BEFORE_OOS","target":"abs_gt_1pct_h3",
"definition":"SPY reaches absolute close-to-reference move >=1% within next 3 sessions",
"features":["ret_1","ret_2","ret_5","ret_10","ret_20","ret_60","gap","intraday","range","atr_14","vol_5","vol_20","vol_60","vol_ratio","close_sma20","close_sma50","drawdown_60","volume_ratio"],
"train_end":"2021-12-31","validation_start":"2022-01-01","validation_end":"2023-12-31","purge_sessions":3,
"model":"deterministic_l2_logistic","l2":src["abs_gt_1pct_h3"]["l2"],"standardization":"fit_train_only",
"selection_metrics":["brier","logloss"],"threshold_policy":"probabilities first; no trading threshold selected",
"oos_start":"2024-01-01","oos_status":"UNOPENED"}
raw=json.dumps(contract,sort_keys=True,separators=(",",":"));contract["sha256"]=hashlib.sha256(raw.encode()).hexdigest()
Path("artifacts/o2").mkdir(parents=True,exist_ok=True);Path("artifacts/o2/O2_H3_MAGNITUDE_V01_FROZEN.json").write_text(json.dumps(contract,indent=2))
print(json.dumps(contract,indent=2))
