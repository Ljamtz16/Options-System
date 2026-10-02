import json,time
from options_system.env import load_local_env
load_local_env()
from options_system.batch_backfill import fetch_bars_batch
p="data/raw/historical/backfill_v01/2024-02/manifests/2024-02-09/universe.json"
u=json.load(open(p))["universe"]
symbols=[r["option_symbol"] for r in u[:20]]
t=time.time()
print(fetch_bars_batch(symbols,"2024-02-09T14:30:00Z","2024-02-09T21:00:00Z",
 "data/raw/historical/batch_probe_2024-02-09",batch_size=20))
print("seconds=",round(time.time()-t,2))
