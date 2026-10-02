import json,time
from datetime import date,timedelta
from pathlib import Path
from options_system.env import load_local_env
load_local_env()
from options_system.session_builder import prepare_session
from options_system.bars_backfill import run_session_bars

def weekdays(year,month):
    d=date(year,month,1)
    while d.month==month:
        if d.weekday()<5: yield d
        d+=timedelta(days=1)

root=Path("data/raw/historical/backfill_v01/2024-02")
summary=[]
for d in weekdays(2024,2):
    ds=d.isoformat()
    start=f"{ds}T14:30:00Z"; end=f"{ds}T21:00:00Z"
    t=time.time()
    try:
        m=prepare_session(ds,start,end,root/"manifests")
        run=run_session_bars(ds,m["universe"],start,end,root/"bars")
        row={"date":ds,"spot":m["decision_reference"]["price"],
             "eligible":m["contract_count"],"completed":run["completed"],
             "failures":len(run["failures"]),"seconds":round(time.time()-t,2)}
    except RuntimeError as exc:
        row={"date":ds,"skipped":True,"reason":str(exc),"seconds":round(time.time()-t,2)}
    summary.append(row); print(row,flush=True)
    (root/"month_summary.json").write_text(json.dumps(summary,indent=2))
print("DONE",flush=True)
