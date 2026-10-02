import json
from options_system.env import load_local_env
from options_system.spy_daily import fetch_daily_spy
from options_system.spy_features import build_features,FEATURES
from options_system.event_labels import event_labels
from options_system.temporal_protocol import add_label_end_dates,temporal_split
from options_system.probability_baseline import fit_standardizer,transform,fit_logistic,predict
from options_system.calibration import fit_platt,apply_platt
from options_system.calibration_metrics import ece
load_local_env();c=json.load(open("artifacts/o2/O2_H3_MAGNITUDE_V01_FROZEN.json"))
rows=fetch_daily_spy("2018-11-01T00:00:00Z","2026-09-01T00:00:00Z");f=build_features(rows);e=event_labels([(r["date"],r["close"]) for r in rows]);ds=[]
for i,r in enumerate(rows):ds.append({**r,**f[i],**{k:v for k,v in e[i].items() if k!="date"}})
u=[r for r in add_label_end_dates(ds) if all(r[k] is not None for k in FEATURES)];s=temporal_split(u,c["train_end"],c["validation_end"],3);target=c["target"]
def xy(q):
 q=[r for r in q if r.get(target) is not None];return [[float(r[k]) for k in FEATURES] for r in q],[1 if r[target] else 0 for r in q],[r["date"] for r in q]
Xt,yt,_=xy(s["train"]);Xv,yv,dv=xy(s["validation"]);Xo,yo,do=xy(s["oos"]);mu,sd=fit_standardizer(Xt)
m=fit_logistic(transform(Xt,mu,sd),yt,l2=c["l2"],lr=.04,steps=1800);pv=predict(m,transform(Xv,mu,sd));po=predict(m,transform(Xo,mu,sd));pl=fit_platt(pv,yv);pvc=apply_platt(pl,pv);poc=apply_platt(pl,po)
out={"validation":{"raw":ece(yv,pv),"platt":ece(yv,pvc)},"oos":{"raw":ece(yo,po),"platt":ece(yo,poc)},"oos_years":{}}
for year in ("2024","2025","2026"):
 ix=[i for i,d in enumerate(do) if d.startswith(year)];yy=[yo[i] for i in ix]
 out["oos_years"][year]={"raw":ece(yy,[po[i] for i in ix]),"platt":ece(yy,[poc[i] for i in ix])}
json.dump(out,open("artifacts/o3/o3_reliability_gate_v01.json","w"),indent=2)
print(json.dumps({"validation_ece":{"raw":out["validation"]["raw"]["ece"],"platt":out["validation"]["platt"]["ece"]},"oos_ece":{"raw":out["oos"]["raw"]["ece"],"platt":out["oos"]["platt"]["ece"]},"years":{y:{"raw":z["raw"]["ece"],"platt":z["platt"]["ece"]} for y,z in out["oos_years"].items()},"platt_oos_bins":out["oos"]["platt"]["bins"]},indent=2))
