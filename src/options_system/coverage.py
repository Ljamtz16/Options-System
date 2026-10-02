import json
from pathlib import Path

def session_coverage(session_root):
    root=Path(session_root); rows=[]
    cp=root/"session_checkpoint.json"
    completed=json.loads(cp.read_text()).get("completed",[]) if cp.exists() else []
    for symbol in completed:
        base=root/symbol
        def records(kind):
            p=base/kind/f"{kind}_manifest.json"
            return json.loads(p.read_text()).get("records",0) if p.exists() else 0
        b,t=records("bars"),records("trades")
        rows.append({"option_symbol":symbol,"bars":b,"trades":t,
                     "has_bars":b>0,"has_trades":t>0})
    return rows
