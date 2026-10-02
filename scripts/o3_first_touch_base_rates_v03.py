import json,collections
from options_system.env import load_local_env
from options_system.spy_daily import fetch_daily_spy
from options_system.open_first_touch import label_family
load_local_env();r=fetch_daily_spy("2018-11-01T00:00:00Z","2026-09-01T00:00:00Z")
parts={"train":lambda d:d<="2021-12-31","validation":lambda d:"2022-01-01"<=d<="2023-12-31","inspected_2024_2026":lambda d:d>="2024-01-01"}
out={}
for pn,pred in parts.items():
 counts={k:collections.Counter() for k in ("sym_05","up10_dn05","up05_dn10","sym_10")}
 offsets={k:collections.Counter() for k in counts}
 for i in range(len(r)-2):
  if not pred(r[i]["date"]):continue
  for k,v in label_family(r,i).items():
   counts[k][v["label"]]+=1
   if v["session_offset"] is not None:offsets[k][str(v["session_offset"])]+=1
 out[pn]={k:{"counts":dict(counts[k]),"rates":{a:n/sum(counts[k].values()) for a,n in counts[k].items()},"touch_offsets":dict(offsets[k])} for k in counts}
open("artifacts/o3_first_touch_base_rates_v03.json","w").write(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
