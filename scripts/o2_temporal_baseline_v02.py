import json
from options_system.env import load_local_env
from options_system.spy_daily import fetch_daily_spy
from options_system.spy_features import build_features,FEATURES
from options_system.event_labels import event_labels
from options_system.temporal_protocol import add_label_end_dates,temporal_split
load_local_env();rows=fetch_daily_spy("2018-11-01T00:00:00Z","2026-09-01T00:00:00Z")
f=build_features(rows);e=event_labels([(r["date"],r["close"]) for r in rows]);ds=[]
for i,r in enumerate(rows):ds.append({**r,**f[i],**{k:v for k,v in e[i].items() if k!="date"}})
u=[r for r in add_label_end_dates(ds) if all(r[k] is not None for k in FEATURES)]
s=temporal_split(u,"2021-12-31","2023-12-31",10)
def stat(x):
 y=[r["up05_dn05_h10"] for r in x if r.get("up05_dn05_h10") in ("UP","DOWN")]
 return {"n":len(y),"up":y.count("UP"),"down":y.count("DOWN"),"up_rate":y.count("UP")/len(y) if y else None}
o={"coverage":[rows[0]["date"],rows[-1]["date"]],"usable":len(u),"protocol":{"train_end":"2021-12-31","validation_end":"2023-12-31","horizon":10},"train":stat(s["train"]),"validation":stat(s["validation"]),"oos":stat(s["oos"])}
open("artifacts/o2/temporal_baseline_v02.json","w").write(json.dumps(o,indent=2));print(json.dumps(o,indent=2))
