import json
from options_system.env import load_local_env
from options_system.spy_daily import fetch_daily_spy
from options_system.open_regime_features import open_regime_features
from options_system.direction_model import fit_logistic,predict,brier,logloss
load_local_env();r=fetch_daily_spy("2018-11-01T00:00:00Z","2026-09-01T00:00:00Z")
data=[]
for i in range(len(r)-2):
 z=open_regime_features(r,i)
 if not z:continue
 base,reg=z;ret=float(r[i+2]["close"])/float(r[i]["open"])-1
 data.append((r[i]["date"],base,reg,1 if ret>0 else 0,ret))
tr=[z for z in data if z[0]<="2021-12-31"];va=[z for z in data if "2022-01-01"<=z[0]<="2023-12-31"];oo=[z for z in data if z[0]>="2024-01-01"]
groups={"base":["ret1","ret2","ret5","ret10","ret20","gap"],"trend":["sma20","sma50","drawdown60"],"volatility":["vol5","vol20","vol60","atr14","prev_range"],"micro_context":["prev_intraday","volume_ratio"]}
specs={"base":groups["base"],"base_trend":groups["base"]+groups["trend"],"base_volatility":groups["base"]+groups["volatility"],"base_micro":groups["base"]+groups["micro_context"],"all":sum(groups.values(),[])}
def run(keys):
 X=lambda z:[(z[1]|z[2])[k] for k in keys];mu=[sum(X(z)[j] for z in tr)/len(tr) for j in range(len(keys))];sd=[(sum((X(z)[j]-mu[j])**2 for z in tr)/(len(tr)-1))**.5 or 1 for j in range(len(keys))]
 S=lambda z:[(X(z)[j]-mu[j])/sd[j] for j in range(len(keys))];w=fit_logistic([S(z) for z in tr],[z[3] for z in tr],steps=1500,lr=.03)
 def M(ds):
  y=[z[3] for z in ds];p=predict(w,[S(z) for z in ds]);bp=sum(z[3] for z in tr)/len(tr);q=[bp]*len(y)
  return {"n":len(y),"up_rate":sum(y)/len(y),"mean_p":sum(p)/len(p),"delta_brier":brier(y,q)-brier(y,p),"delta_logloss":logloss(y,q)-logloss(y,p)}
 return {"features":keys,"train":M(tr),"validation":M(va),"inspected_2024_2026":M(oo)}
out={k:run(v) for k,v in specs.items()}
open("artifacts/o3_direction_regime_ablation_v02.json","w").write(json.dumps(out,indent=2));print(json.dumps({k:v["validation"] for k,v in out.items()},indent=2))
