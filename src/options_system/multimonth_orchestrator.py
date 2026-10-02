import json,time,calendar
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from .market_calendar import market_calendar
from .session_builder import prepare_session
from .batch_backfill import fetch_bars_batch

NY=ZoneInfo("America/New_York")
def utc_stamp(day,hhmm):
    local=datetime.fromisoformat(f"{day}T{hhmm}:00").replace(tzinfo=NY)
    return local.astimezone(ZoneInfo("UTC")).isoformat().replace("+00:00","Z")

def run_month(year,month,root_dir,manifest_root,batch_size=100):
    first=f"{year:04d}-{month:02d}-01"; last=f"{year:04d}-{month:02d}-{calendar.monthrange(year,month)[1]:02d}"
    days=market_calendar(first,last); root=Path(root_dir)/f"{year:04d}-{month:02d}"; root.mkdir(parents=True,exist_ok=True)
    rows=[]
    for x in days:
        ds=x["date"]; start=utc_stamp(ds,x["open"]); end=utc_stamp(ds,x["close"]); t=time.time()
        m=prepare_session(ds,start,end,Path(manifest_root)/f"{year:04d}-{month:02d}")
        syms=[r["option_symbol"] for r in m["universe"]]
        r=fetch_bars_batch(syms,start,end,root/ds,batch_size=batch_size)
        rows.append({"date":ds,"open_utc":start,"close_utc":end,"eligible":len(syms),
          "batches":r["batches"],"completed":r["completed"],"seconds":round(time.time()-t,2)})
        (root/"month_summary.json").write_text(json.dumps(rows,indent=2)); time.sleep(8)
    return rows
