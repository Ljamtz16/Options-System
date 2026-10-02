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
targets=[]
for h in (1,3,5,10):
 for fam in ("up05_dn05","up10_dn05","up05_dn10"):targets.append((f"{fam}_h{h}",h,"UP","DOWN"))
 targets.append((f"abs_gt_1pct_h{h}",h,"True","False"))
results=[]
for target,h,pos,neg in targets:
 s=temporal_split(u,"2021-12-31","2023-12-31",h)
 def xy(part):
  q=[r for r in part if str(r.get(target)) in (pos,neg)]
  return [[float(r[k]) for k in FEATURES] for r in q],[1 if str(r[target])==pos else 0 for r in q]
 Xt,yt=xy(s["train"]);Xv,yv=xy(s["validation"])
 if not Xt or not Xv or len(set(yt))<2:
  results.append({"target":target,"status":"DEGENERATE_OR_EMPTY","train_n":len(yt),"val_n":len(yv)});continue
 mu,sd=fit_standardizer(Xt);Xt=transform(Xt,mu,sd);Xv=transform(Xv,mu,sd);bp=sum(yt)/len(yt);bm=metrics(yv,[bp]*len(yv))
 best=None
 for l2 in (.1,1.,10.):
  m=fit_logistic(Xt,yt,l2=l2,lr=.04,steps=1800);mm=metrics(yv,predict(m,Xv))
  if best is None or mm["brier"]<best["metrics"]["brier"]:best={"l2":l2,"metrics":mm}
 supported=best["metrics"]["brier"]<bm["brier"] and best["metrics"]["logloss"]<bm["logloss"]
 results.append({"target":target,"train_n":len(yt),"val_n":len(yv),"train_rate":bp,"baseline":bm,"best":best,"supported":supported})
open("artifacts/o2/o2_target_sweep_v01.json","w").write(json.dumps(results,indent=2))
print(json.dumps([{"target":r["target"],"status":r.get("status"),"n":r.get("val_n"),"base_brier":r.get("baseline",{}).get("brier"),"best_brier":r.get("best",{}).get("metrics",{}).get("brier"),"base_ll":r.get("baseline",{}).get("logloss"),"best_ll":r.get("best",{}).get("metrics",{}).get("logloss"),"supported":r.get("supported")} for r in results],indent=2))
