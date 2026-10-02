import json
from pathlib import Path

FIELDS=("timestamp","option_symbol","option_type","strike","expiration_date","dte",
        "spot_reference","open","high","low","close","volume","trade_count","vwap")

def normalize_session(raw_dir,universe_manifest):
    manifest=json.loads(Path(universe_manifest).read_text())
    meta={r["option_symbol"]:r for r in manifest["universe"]}; rows=[]
    for p in sorted(Path(raw_dir).glob("batch_*_page_*.json")):
        payload=json.loads(p.read_text())["payload"].get("bars",{})
        for symbol,bars in payload.items():
            if symbol not in meta: raise ValueError(f"Unexpected symbol: {symbol}")
            m=meta[symbol]
            for b in bars:
                rows.append({"timestamp":b["t"],"option_symbol":symbol,"option_type":m["option_type"],
                  "strike":m["strike"],"expiration_date":m["expiration_date"],"dte":m["dte"],
                  "spot_reference":m["spot_reference"],"open":b["o"],"high":b["h"],"low":b["l"],
                  "close":b["c"],"volume":b["v"],"trade_count":b.get("n"),"vwap":b.get("vw")})
    rows.sort(key=lambda r:(r["timestamp"],r["option_symbol"]))
    keys=[(r["timestamp"],r["option_symbol"]) for r in rows]
    if len(keys)!=len(set(keys)): raise ValueError("Duplicate timestamp/symbol rows")
    return rows
