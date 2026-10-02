from .intraday_contracts import _meta

DELTA_TARGETS=(.25,.40,.50,.60)
DTE_BUCKETS=((0,0),(1,1),(2,3),(4,7))

def contract_candidates(chain_snapshot,market_date):
    rows=[]
    for sym,s in ((chain_snapshot or {}).get("snapshots") or {}).items():
        meta=_meta(sym,market_date)
        if not meta or not (0<=meta["dte"]<=7):continue
        g=s.get("greeks") or {};q=s.get("latestQuote") or {}
        delta=g.get("delta");bid=q.get("bp");ask=q.get("ap")
        if delta is None or bid is None or ask is None:continue
        bid=float(bid);ask=float(ask)
        if ask<=0 or bid<=0 or ask<bid:continue
        spread=(ask-bid)/((ask+bid)/2)
        rows.append({**meta,"symbol":sym,"delta":float(delta),
                     "bid":bid,"ask":ask,"spread_pct":spread})
    return rows

def select_grid(chain_snapshot,market_date,max_spread=.25):
    rows=contract_candidates(chain_snapshot,market_date);out={}
    for side in ("call","put"):
        sr=[r for r in rows if r["side"]==side and r["spread_pct"]<=max_spread]
        for target in DELTA_TARGETS:
            for lo,hi in DTE_BUCKETS:
                ss=[r for r in sr if lo<=r["dte"]<=hi]
                if not ss:continue
                best=min(ss,key=lambda r:abs(abs(r["delta"])-target))
                key=f"{side}_{int(target*100)}d_dte{lo}_{hi}"
                out[key]=best
    return out