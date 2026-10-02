import json
from options_system.env import load_local_env
from options_system.spy_daily import fetch_daily_spy
from options_system.spy_features import build_features,FEATURES
from options_system.event_labels import event_labels
from options_system.temporal_protocol import add_label_end_dates,temporal_split
load_local_env()
rows=fetch_daily_spy("2016-01-01T00:00:00Z","2026-09-01T00:00:00Z")
features=build_features(rows); labels=event_labels([(r["date"],r["close"]) for r in rows])
ds=[]
for i,r in enumerate(rows):
 z={**r,**features[i],**{k:v for k,v in labels[i].items() if k!="date"}}
 ds.append(z)
ds=add_label_end_dates(ds)
usable=[r for r in ds if all(r[k] is not None for k in FEATURES)]
s=temporal_split(usable,"2019-12-31","2021-12-31",10)
def base(x):
 y=[r["up05_dn05_h10"] for r in x if r.get("up05_dn05_h10") in ("UP","DOWN")]
 return {"n":len(y),"up":sum(v=="UP" for v in y),"down":sum(v=="DOWN" for v in y),
 "up_rate":sum(v=="UP" for v in y)/len(y) if y else None}
out={"source_rows":len(rows),"usable":len(usable),"train":base(s["train"]),"validation":base(s["validation"]),"oos":base(s["oos"]),
"boundaries":{"train_end":"2019-12-31","validation_end":"2021-12-31","purge_horizon":10}}
print(json.dumps(out,indent=2))
open("artifacts/o2/temporal_baseline_v01.json","w").write(json.dumps(out,indent=2))
