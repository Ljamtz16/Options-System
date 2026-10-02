import json
from pathlib import Path
from options_system.env import load_local_env
from options_system.alpaca_history import fetch_json
load_local_env()
m=json.load(open("data/raw/historical/backfill_v01/2024-02/manifests/2024-02-02/universe.json"))
symbols=[x["option_symbol"] for x in m["universe"]]
sample=[symbols[0],symbols[len(symbols)//2],symbols[-1]]
for s in sample:
 print("SYMBOL",s,flush=True)
 for kind in ("bars","trades"):
  p={"symbols":s,"start":"2024-02-02T14:30:00Z","end":"2024-02-02T21:00:00Z","limit":1000}
  if kind=="bars": p["timeframe"]="1Min"
  x,u=fetch_json(kind,p); rows=x.get(kind,{}).get(s,[])
  print(kind,len(rows),rows[:1],flush=True)
