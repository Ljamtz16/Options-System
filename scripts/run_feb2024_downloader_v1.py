import json,time
from datetime import date,timedelta
from pathlib import Path
from options_system.env import load_local_env
load_local_env()
from options_system.session_builder import prepare_session
from options_system.batch_backfill import fetch_bars_batch
manifest_root=Path("data/raw/historical/backfill_v01/2024-02/manifests")
out=Path("data/raw/historical/downloader_v1/2024-02"); rows=[]
d=date(2024,2,1)
while d.month==2:
    if d.weekday()<5:
        ds=d.isoformat(); start=f"{ds}T14:30:00Z"; end=f"{ds}T21:00:00Z"; t=time.time()
        try:
            print(f"SESSION {ds} START",flush=True)
            m=prepare_session(ds,start,end,manifest_root)
            symbols=[r["option_symbol"] for r in m["universe"]]
            r=fetch_bars_batch(symbols,start,end,out/ds,batch_size=100,
                log_fn=lambda x,ds=ds: print(f"{ds} {x}",flush=True))
            row={"date":ds,"eligible":len(symbols),"batches":r["batches"],
                 "completed_batches":r["completed"],"seconds":round(time.time()-t,2)}
            print("SESSION DONE",row,flush=True)
            time.sleep(8)
        except RuntimeError as exc:
            row={"date":ds,"skipped":True,"reason":str(exc)}
            print("SESSION SKIP",row,flush=True)
        rows.append(row); (out/"month_summary.json").write_text(json.dumps(rows,indent=2))
    d+=timedelta(days=1)
print("MONTH LOOP DONE",flush=True)
