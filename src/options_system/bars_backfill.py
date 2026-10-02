import json,time
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
from urllib.error import HTTPError
from .historical_backfill import fetch_pages

def run_session_bars(session_date,universe,start_utc,end_utc,root_dir,workers=2,retries=6):
    root=Path(root_dir)/session_date; root.mkdir(parents=True,exist_ok=True)
    cp=root/"bars_checkpoint.json"; done=set()
    if cp.exists(): done=set(json.loads(cp.read_text()).get("completed",[]))
    failures=[]; pending=[r["option_symbol"] for r in universe if r["option_symbol"] not in done]
    def one(symbol):
        for attempt in range(retries+1):
            try:
                fetch_pages("bars",symbol,start_utc,end_utc,root/symbol/"bars",resume=True)
                time.sleep(0.15); return symbol
            except FileExistsError:
                return symbol
            except HTTPError as exc:
                if attempt==retries: raise
                wait=max(2**attempt,5) if exc.code==429 else 2**attempt
                time.sleep(wait)
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures={ex.submit(one,s):s for s in pending}
        for f in as_completed(futures):
            symbol=futures[f]
            try: done.add(f.result())
            except HTTPError as exc: failures.append({"symbol":symbol,"error":"HTTPError","code":exc.code})
            except Exception as exc: failures.append({"symbol":symbol,"error":type(exc).__name__})
            cp.write_text(json.dumps({"completed":sorted(done),"failures":failures},indent=2))
    return {"selected":len(universe),"completed":len(done),"failures":failures}
