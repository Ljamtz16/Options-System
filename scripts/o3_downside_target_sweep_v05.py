import csv,json
from options_system.direction_model import fit_logistic,predict,brier,logloss
from options_system.spy_open_features import FEATURE_NAMES
from options_system.open_first_touch import first_touch_open
from options_system.env import load_local_env
from options_system.spy_daily import fetch_daily_spy
load_local_env()
daily=fetch_daily_spy("2018-11-01T00:00:00Z","2026-09-01T00:00:00Z")
D=list(csv.DictReader(open("data/processed/o2_open/spy_open_outcomes_v02.csv")))
bydate={z["decision_date"]:z for z in D}
def label(z,name):
 d=z["decision_date"];i=next(i for i,r in enumerate(daily) if r["date"]==d)
 if name=="mae_1pct_h3": return 1 if float(z["mae_h3"])<=-.01 else 0
 if name=="down05_before_up05":
  v=first_touch_open(daily,i,3,.005,.005)
  return 1 if v["label"]=="DOWN" else 0
 if name=="down10_before_up05":
  v=first_touch_open(daily,i,3,.005,.01)
  return 1 if v["label"]=="DOWN" else 0
 raise ValueError(name)
targets=("mae_1pct_h3","down05_before_up05","down10_before_up05")
out={}
for name in targets:
 rows=[z for z in D if z["label_end_h3"]]
 tr=[z for z in rows if z["decision_date"]<="2021-12-31"];va=[z for z in rows if "2022-01-01"<=z["decision_date"]<="2023-12-31"];dg=[z for z in rows if z["decision_date"]>="2024-01-01"]
 X=lambda z:[float(z[k]) for k in FEATURE_NAMES]
 mu=[sum(X(z)[j] for z in tr)/len(tr) for j in range(len(FEATURE_NAMES))]
 sd=[(sum((X(z)[j]-mu[j])**2 for z in tr)/(len(tr)-1))**.5 or 1 for j in range(len(mu))]
 S=lambda z:[(X(z)[j]-mu[j])/sd[j] for j in range(len(mu))]
 yt=[label(z,name) for z in tr];w=fit_logistic([S(z) for z in tr],yt,steps=1400,lr=.03)
 def M(ds):
  y=[label(z,name) for z in ds];p=predict(w,[S(z) for z in ds]);base=sum(yt)/len(yt);q=[base]*len(y)
  return {"n":len(y),"train_base":base,"event_rate":sum(y)/len(y),"mean_p":sum(p)/len(p),
  "delta_brier":brier(y,q)-brier(y,p),"delta_logloss":logloss(y,q)-logloss(y,p)}
 out[name]={"train":M(tr),"validation":M(va),"inspected_2024_2026":M(dg)}
open("artifacts/o3_downside_target_sweep_v05.json","w").write(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
