import json,time
from options_system.env import load_local_env
load_local_env()
from options_system.batch_backfill import fetch_bars_batch
d="2024-02-09"
u=json.load(open(f"data/raw/historical/backfill_v01/2024-02/manifests/{d}/universe.json"))["universe"]
symbols=[r["option_symbol"] for r in u]
t=time.time()
r=fetch_bars_batch(symbols,f"{d}T14:30:00Z",f"{d}T21:00:00Z",
 f"data/raw/historical/backfill_batch_v01/2024-02/{d}",batch_size=20)
print("contracts=",len(symbols),r,"seconds=",round(time.time()-t,2),flush=True)
