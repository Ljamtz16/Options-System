from .stock_history import stock_bars

def causal_spot_reference(symbol,start_utc,end_utc):
    payload,url=stock_bars(symbol,start_utc,end_utc)
    bars=payload.get("bars",{}).get(symbol,[])
    if not bars: raise RuntimeError("No contemporaneous SPY bar available")
    first=bars[0]
    return {"price":float(first["o"]),"observed_at_utc":first["t"],
            "basis":"first_1min_bar_open","feed":"iex","source_url":url}

def spy_reference_at(symbol,start_utc,end_utc):
    r=causal_spot_reference(symbol,start_utc,end_utc)
    return {"price":r["price"],"timestamp":r["observed_at_utc"],
            "field":"open","source_url":r["source_url"]}

def spy_session_bars(symbol,start_utc,end_utc):
    payload,url=stock_bars(symbol,start_utc,end_utc)
    return payload.get("bars",{}).get(symbol,[]),url
