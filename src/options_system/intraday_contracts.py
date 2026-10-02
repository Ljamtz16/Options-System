import re
from datetime import datetime

_OCC=re.compile(r"^([A-Z]+)(\d{6})([CP])(\d{8})$")

def _meta(symbol,market_date):
    m=_OCC.match(symbol)
    if not m:return None
    _,ds,cp,strike=m.groups()
    exp=datetime.strptime(ds,"%y%m%d").date()
    return {"side":"call" if cp=="C" else "put",
            "strike":int(strike)/1000.0,
            "dte":(exp-market_date).days}

def representative_contracts(chain_snapshot,market_date):
    rows=[]
    for sym,s in ((chain_snapshot or {}).get("snapshots") or {}).items():
        meta=_meta(sym,market_date)
        if not meta or not (0<=meta["dte"]<=7):continue
        delta=(s.get("greeks") or {}).get("delta")
        q=s.get("latestQuote") or {}
        bid,ask=q.get("bp"),q.get("ap")
        if delta is None or not bid or not ask or ask<bid:continue
        rows.append({**meta,"symbol":sym,"delta":float(delta),
                     "bid":float(bid),"ask":float(ask),
                     "bid_size":q.get("bs"),"ask_size":q.get("as"),
                     "iv":s.get("impliedVolatility")})
    out={}
    for side in ("call","put"):
        ss=[r for r in rows if r["side"]==side]
        if not ss:
            out[side]=None
            continue
        ss.sort(key=lambda r:(r["dte"],abs(abs(r["delta"])-.50)))
        out[side]=ss[0]
    return out

def conservative_long_pnl(entry,exit_snapshot):
    if not entry:return None
    s=((exit_snapshot or {}).get("snapshots") or {}).get(entry["symbol"])
    if not s:return None
    q=s.get("latestQuote") or {}
    exit_bid=q.get("bp")
    if exit_bid is None or float(exit_bid)<=0:return None
    cost=float(entry["ask"])*100
    pnl=(float(exit_bid)-float(entry["ask"]))*100
    return {"contract":entry["symbol"],"entry_ask":float(entry["ask"]),
            "exit_bid":float(exit_bid),"pnl_usd":pnl,
            "return":pnl/cost if cost>0 else None}
