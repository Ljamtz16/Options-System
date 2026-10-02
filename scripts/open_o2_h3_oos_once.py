import json,hashlib
from pathlib import Path
from options_system.env import load_local_env
from options_system.spy_daily import fetch_daily_spy
from options_system.spy_features import build_features,FEATURES
from options_system.event_labels import event_labels
from options_system.temporal_protocol import add_label_end_dates,temporal_split
from options_system.probability_baseline import fit_standardizer,transform,fit_logistic,predict,metrics
from options_system.validation_metrics import auc_rank,calibration_bins
load_local_env();contract=json.load(open("artifacts/o2/O2_H3_MAGNITUDE_V01_FROZEN.json"))
rows=fetch_daily_spy("2018-11-01T00:00:00Z","2026-09-01T00:00:00Z");f=build_features(rows);e=event_labels([(r["date"],r["close"]) for r in rows]);ds=[]
for i,r in enumerate(rows):ds.append({**r,**f[i],**{k:v for k,v in e[i].items() if k!="date"}})
u=[r for r in add_label_end_dates(ds) if all(r[k] is not None for k in FEATURES)]
s=temporal_split(u,contract["train_end"],contract["validation_end"],3);target=contract["target"]
def xy(q):
 q=[r for r in q if r.get(target) is not None]
 return [[float(r[k]) for k in FEATURES] for r in q],[1 if r[target] else 0 for r in q],[r["date"] for r in q]
Xt,yt,_=xy(s["train"]);Xo,yo,do=xy(s["oos"]);mu,sd=fit_standardizer(Xt);model=fit_logistic(transform(Xt,mu,sd),yt,l2=contract["l2"],lr=.04,steps=1800);po=predict(model,transform(Xo,mu,sd));bp=sum(yt)/len(yt)
def report(ix):
 y=[yo[i] for i in ix];p=[po[i] for i in ix];base=metrics(y,[bp]*len(y));mod=metrics(y,p)
 return {"baseline":base,"model":mod,"delta_brier":base["brier"]-mod["brier"],"delta_logloss":base["logloss"]-mod["logloss"],"auc":auc_rank(y,p),"calibration":calibration_bins(y,p)}
out={"contract_id":contract["id"],"contract_sha256":contract["sha256"],"oos_opened":True,"overall":report(list(range(len(yo)))),"years":{}}
for year in ("2024","2025","2026"):
 ix=[i for i,d in enumerate(do) if d.startswith(year)]
 if ix:out["years"][year]=report(ix)
raw=json.dumps(out,sort_keys=True,separators=(",",":"));out["result_sha256"]=hashlib.sha256(raw.encode()).hexdigest()
Path("artifacts/o2/O2_H3_MAGNITUDE_V01_OOS_RESULT.json").write_text(json.dumps(out,indent=2))
print(json.dumps({"overall":out["overall"],"years":{y:{"n":z["model"]["n"],"dB":round(z["delta_brier"],5),"dLL":round(z["delta_logloss"],5),"auc":round(z["auc"],4),"event_rate":round(z["model"]["event_rate"],4),"mean_p":round(z["model"]["mean_p"],4)} for y,z in out["years"].items()},"result_sha256":out["result_sha256"]},indent=2))
