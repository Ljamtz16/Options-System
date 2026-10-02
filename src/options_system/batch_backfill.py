import json,time
from pathlib import Path
from urllib.error import HTTPError
from .alpaca_history import fetch_json,save_snapshot

def fetch_bars_batch(symbols,start,end,output_dir,batch_size=100,retries=8,sleep_fn=time.sleep,log_fn=print):
    root=Path(output_dir); root.mkdir(parents=True,exist_ok=True)
    cp=root/"batch_checkpoint.json"
    state=json.loads(cp.read_text()) if cp.exists() else {"completed_batches":[]}
    done=set(state.get("completed_batches",[]))
    total=(len(symbols)+batch_size-1)//batch_size
    for i in range(0,len(symbols),batch_size):
        batch=symbols[i:i+batch_size]; bid=f"{i//batch_size:04d}"
        if bid in done: continue
        token=None; page=0
        while True:
            params={"symbols":",".join(batch),"timeframe":"1Min","start":start,"end":end,"limit":10000}
            if token: params["page_token"]=token
            for attempt in range(retries+1):
                try: payload,url=fetch_json("bars",params); break
                except HTTPError as exc:
                    if attempt==retries: raise
                    wait=max(5,min(60,2**attempt)) if exc.code==429 else min(30,2**attempt)
                    log_fn(f"HTTP {exc.code} batch={bid} attempt={attempt+1} wait={wait}s")
                    sleep_fn(wait)
            page+=1; out=root/f"batch_{bid}_page_{page:04d}.json"
            if not out.exists(): save_snapshot(payload,url,out)
            token=payload.get("next_page_token")
            if not token: break
        done.add(bid)
        cp.write_text(json.dumps({"completed_batches":sorted(done),"batch_size":batch_size,
          "symbol_count":len(symbols),"total_batches":total},indent=2))
        log_fn(f"batch {len(done)}/{total} complete")
        sleep_fn(1.0)
    return {"batches":total,"completed":len(done),"symbols":len(symbols)}
