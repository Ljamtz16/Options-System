import json
from options_system.env import load_local_env
from options_system.spy_daily import fetch_daily_spy
from options_system.spy_features import build_features,FEATURES
from options_system.event_labels import event_labels
from options_system.temporal_protocol import add_label_end_dates,temporal_split
from options_system.probability_baseline import fit_standardizer,transform,fit_logistic,predict,metrics
load_local_env();rows=fetch_daily_spy("2018-11-01T00:00:00Z","2026-09-01T00:00:00Z")
f=build_features(rows);e=event_labels([(r["date"],r["close"]) for r in rows]);ds=[]
for i,r in enumerate(rows):ds.append({**r,**f[i],**{k:v for k,v in e[i].items() if k!="date"}})
u=[r for r in add_label_end_dates(ds) if all(r[k] is not None for k in FEATURES)]
s=temporal_split(u,"2021-12-31","2023-12-31",10)
def xy(part):
 q=[r for r in part if r.get("up05_dn05_h10") in ("UP","DOWN")]
 return [[float(r[k]) for k in FEATURES] for r in q],[1 if r["up05_dn05_h10"]=="UP" else 0 for r in q]
Xt,yt=xy(s["train"]);Xv,yv=xy(s["validation"]);mu,sd=fit_standardizer(Xt);Xt=transform(Xt,mu,sd);Xv=transform(Xv,mu,sd)
base=sum(yt)/len(yt);result={"baseline_p":base,"baseline_validation":metrics(yv,[base]*len(yv)),"models":{}}
for l2 in (.001,.01,.1,1.0,10.0):
 m=fit_logistic(Xt,yt,l2=l2);result["models"][str(l2)]={"validation":metrics(yv,predict(m,Xv)),"model":m}
best=min(result["models"],key=lambda k:result["models"][k]["validation"]["brier"]);result["selected_l2"]=best
open("artifacts/o2/o2_validation_model_selection_v01.json","w").write(json.dumps(result,indent=2))
print(json.dumps({"baseline":result["baseline_validation"],"models":{k:v["validation"] for k,v in result["models"].items()},"selected_l2":best},indent=2))
