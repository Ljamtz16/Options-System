import json
from options_system.env import load_local_env
from options_system.spy_daily import fetch_daily_spy
from options_system.open_regime_features import open_regime_features
from options_system.regime_direction import regime_key,fit_regime_table,predict_regime
from options_system.direction_model import brier,logloss
load_local_env();r=fetch_daily_spy("2018-11-01T00:00:00Z","2026-09-01T00:00:00Z");d=[]
for i in range(len(r)-2):
 z=open_regime_features(r,i)
 if z:
  b,g=z;ret=float(r[i+2]["close"])/float(r[i]["open"])-1;d.append({"date":r[i]["date"],"regime":regime_key(b,g),"up":1 if ret>0 else 0})
tr=[x for x in d if x["date"]<="2021-12-31"];va=[x for x in d if "2022-01-01"<=x["date"]<="2023-12-31"];oo=[x for x in d if x["date"]>="2024-01-01"]
out={}
for a in (10,20,40,80,160):
 m=fit_regime_table(tr,a)
 def M(ds):
  y=[x["up"] for x in ds];p=[predict_regime(m,x["regime"]) for x in ds];q=[m["global_p"]]*len(y)
  return {"n":len(y),"mean_p":sum(p)/len(p),"delta_brier":brier(y,q)-brier(y,p),"delta_logloss":logloss(y,q)-logloss(y,p)}
 out[str(a)]={"validation":M(va),"inspected_2024_2026":M(oo)}
open("artifacts/o3_direction_regime_discrete_v02.json","w").write(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
