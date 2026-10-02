import csv,json
from pathlib import Path
from options_system.env import load_local_env
from options_system.spy_daily import fetch_daily_spy
from options_system.spy_features import build_features,FEATURES
from options_system.outcomes import forward_returns,path_outcomes
from options_system.event_labels import event_labels
load_local_env()
rows=fetch_daily_spy("2023-08-01T00:00:00Z","2024-05-01T00:00:00Z"); closes=[(x["date"],x["close"]) for x in rows]
f=build_features(rows); rets=forward_returns(closes,(1,3,5,10)); paths=path_outcomes(closes,10,.005,.005); events=event_labels(closes)
out=[]
for i in range(len(rows)):
 z={**rows[i],**f[i],**{k:v for k,v in rets[i].items() if k.startswith("ret_h")},
    **{k:v for k,v in paths[i].items() if k!="date"},**{k:v for k,v in events[i].items() if k!="date"}}
 if z["date"]>="2024-02-01":out.append(z)
p=Path("data/processed/o2");p.mkdir(parents=True,exist_ok=True);fields=list(out[0])
with (p/"spy_outcomes_v01.csv").open("w",newline="",encoding="utf-8") as h:
 w=csv.DictWriter(h,fieldnames=fields);w.writeheader();w.writerows(out)
print(json.dumps({"rows":len(out),"features_complete":sum(all(x[k] is not None for k in FEATURES) for x in out),
"h10_complete":sum(x["ret_h10"] is not None for x in out),"columns":len(fields)},indent=2))
