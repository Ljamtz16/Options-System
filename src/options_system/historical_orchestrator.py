import json
from pathlib import Path
from .historical_backfill import fetch_pages

def run_session(session_date, universe, start_utc, end_utc, root_dir, max_contracts=None):
    root=Path(root_dir)/session_date
    root.mkdir(parents=True,exist_ok=True)
    checkpoint=root/"session_checkpoint.json"
    done=set()
    if checkpoint.exists():
        done=set(json.loads(checkpoint.read_text()).get("completed",[]))
    selected=universe[:max_contracts] if max_contracts else universe
    completed=list(done); failures=[]
    for row in selected:
        symbol=row["option_symbol"]
        if symbol in done: continue
        try:
            base=root/symbol
            fetch_pages("bars",symbol,start_utc,end_utc,base/"bars",resume=True)
            fetch_pages("trades",symbol,start_utc,end_utc,base/"trades",resume=True)
            completed.append(symbol); done.add(symbol)
            checkpoint.write_text(json.dumps({"completed":completed,"failures":failures},indent=2))
        except Exception as exc:
            failures.append({"symbol":symbol,"error":type(exc).__name__})
            checkpoint.write_text(json.dumps({"completed":completed,"failures":failures},indent=2))
    return {"selected":len(selected),"completed":len(done.intersection(r["option_symbol"] for r in selected)),
            "failures":failures}
