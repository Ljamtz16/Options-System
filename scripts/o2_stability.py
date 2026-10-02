import json
from options_system.env import load_local_env
from options_system.spy_daily import fetch_daily_spy
from options_system.spy_features import build_features,FEATURES
from options_system.event_labels import event_labels
from options_system.temporal_protocol import add_label_end_dates,temporal_split
from options_system.probability_baseline import fit_standardizer,transform,fit_logistic,predict,metrics
from options_system.validation_metrics import auc_rank,calibration_bins
load_local_env();rows=fetch_daily_spy("2018-11-01T00:00:00Z","2024-01-01T00:00:00Z")
f=build_features(rows);e=event_labels([(r["date"],r["close"]) for r in rows]);ds=[]
for i,r in enumerate(rows):ds.append({**r,**f[i],**{k:v for k,v in e[i].items() if k!="date"}})
u=[r for r in add_label_end_dates(ds) if all(r[k] is not None for k in FEATURES)]
res={}
for h in (1,3,5):
 s=temporal_split(u,"2021-12-31","2023-12-31",h);target=f"abs_gt_1pct_h{h}"
 def xy(q):
  q=[r for r in q if r.get(target) is not None]
  return [[float(r[k]) for k in FEATURES] for r in q],[1 if r[target] else 0 for r in q],[r["date"] for r in q]
 Xt,yt,_=xy(s["train"]);Xv,yv,dv=xy(s["validation"]);mu,sd=fit_standardizer(Xt);Xt=transform(Xt,mu,sd);Xv=transform(Xv,mu,sd)
 bp=sum(yt)/len(yt);best=None
 for l2 in (.1,1.,10.):
  m=fit_logistic(Xt,yt,l2=l2,lr=.04,steps=1800);p=predict(m,Xv);mm=metrics(yv,p)
  if best is None or mm["brier"]<best["all"]["brier"]:best={"l2":l2,"model":m,"p":p,"all":mm}
 years={}
 for year in ("2022","2023"):
  ix=[i for i,d in enumerate(dv) if d.startswith(year)];yy=[yv[i] for i in ix];pp=[best["p"][i] for i in ix]
  bm=metrics(yy,[bp]*len(yy));mm=metrics(yy,pp)
  years[year]={"baseline":bm,"model":mm,"delta_brier":bm["brier"]-mm["brier"],"delta_logloss":bm["logloss"]-mm["logloss"],"auc":auc_rank(yy,pp),"calibration":calibration_bins(yy,pp)}
 res[target]={"l2":best["l2"],"train_rate":bp,"validation":best["all"],"years":years}
open("artifacts/o2/o2_stability_v01.json","w").write(json.dumps(res,indent=2))
print(json.dumps({k:{"l2":v["l2"],"all":v["validation"],"years":{y:{"dB":round(z["delta_brier"],4),"dLL":round(z["delta_logloss"],4),"auc":round(z["auc"],4)} for y,z in v["years"].items()}} for k,v in res.items()},indent=2))
