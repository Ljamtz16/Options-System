import json
from options_system.env import load_local_env
from options_system.spy_daily import fetch_daily_spy
from options_system.spy_features import build_features,FEATURES
from options_system.event_labels import event_labels
from options_system.temporal_protocol import add_label_end_dates,temporal_split
from options_system.probability_baseline import fit_standardizer,transform,fit_logistic,predict,metrics
from options_system.validation_metrics import auc_rank,calibration_bins
from options_system.calibration import fit_platt,apply_platt,fit_temperature,apply_temperature
load_local_env();c=json.load(open("artifacts/o2/O2_H3_MAGNITUDE_V01_FROZEN.json"))
rows=fetch_daily_spy("2018-11-01T00:00:00Z","2026-09-01T00:00:00Z");f=build_features(rows);e=event_labels([(r["date"],r["close"]) for r in rows]);ds=[]
for i,r in enumerate(rows):ds.append({**r,**f[i],**{k:v for k,v in e[i].items() if k!="date"}})
u=[r for r in add_label_end_dates(ds) if all(r[k] is not None for k in FEATURES)];s=temporal_split(u,c["train_end"],c["validation_end"],3);target=c["target"]
def xy(q):
 q=[r for r in q if r.get(target) is not None];return [[float(r[k]) for k in FEATURES] for r in q],[1 if r[target] else 0 for r in q],[r["date"] for r in q]
Xt,yt,_=xy(s["train"]);Xv,yv,_=xy(s["validation"]);Xo,yo,do=xy(s["oos"]);mu,sd=fit_standardizer(Xt)
m=fit_logistic(transform(Xt,mu,sd),yt,l2=c["l2"],lr=.04,steps=1800);pv=predict(m,transform(Xv,mu,sd));po=predict(m,transform(Xo,mu,sd))
cal={"none":None,"platt":fit_platt(pv,yv),"temperature":fit_temperature(pv,yv)}
def app(k,model,p):return p if k=="none" else apply_platt(model,p) if k=="platt" else apply_temperature(model,p)
vr={k:metrics(yv,app(k,v,pv)) for k,v in cal.items()};chosen=min(vr,key=lambda k:(vr[k]["brier"],vr[k]["logloss"]))
poc=app(chosen,cal[chosen],po);out={"validation":vr,"selected":chosen,"calibrator":cal[chosen],"oos":metrics(yo,poc),"oos_auc":auc_rank(yo,poc),"oos_calibration":calibration_bins(yo,poc),"oos_years":{}}
for y in ("2024","2025","2026"):
 ix=[i for i,d in enumerate(do) if d.startswith(y)];yy=[yo[i] for i in ix];pp=[poc[i] for i in ix];out["oos_years"][y]={"metrics":metrics(yy,pp),"auc":auc_rank(yy,pp)}
open("artifacts/o3/o3_calibration_v01.json","w").write(json.dumps(out,indent=2))
print(json.dumps({"validation":vr,"selected":chosen,"calibrator":cal[chosen],"oos":out["oos"],"oos_auc":out["oos_auc"],"years":out["oos_years"]},indent=2))
