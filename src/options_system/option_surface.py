import math,re
from datetime import datetime
_OCC=re.compile(r"^([A-Z]+)(\d{6})([CP])(\d{8})$")
def _median(xs):
 xs=sorted(float(x) for x in xs if x is not None and math.isfinite(float(x)))
 if not xs:return None
 n=len(xs);m=n//2
 return xs[m] if n%2 else (xs[m-1]+xs[m])/2
def _meta(sym,market_date):
 m=_OCC.match(sym)
 if not m:return None
 _,ds,cp,strike=m.groups();exp=datetime.strptime(ds,"%y%m%d").date()
 return {"side":"call" if cp=="C" else "put","strike":int(strike)/1000.0,"dte":(exp-market_date).days}
def _delta_slice(rows,target):
 lo,hi=((.20,.30) if target==.25 else (.40,.60))
 band=[r for r in rows if r["delta"] is not None and lo<=abs(float(r["delta"]))<=hi]
 if band:return band
 eligible=[r for r in rows if r["delta"] is not None]
 if not eligible:return []
 best=min(abs(abs(float(r["delta"]))-target) for r in eligible)
 return [r for r in eligible if abs(abs(float(r["delta"]))-target)<=best+1e-12]
def extract_option_surface(chain_snapshot,spot,market_date):
 rows=[]
 for sym,s in ((chain_snapshot or {}).get("snapshots") or {}).items():
  m=_meta(sym,market_date)
  if not m:continue
  g=s.get("greeks") or {};q=s.get("latestQuote") or {};bar=s.get("dailyBar") or {}
  delta=g.get("delta");iv=s.get("impliedVolatility");b=q.get("bp");a=q.get("ap")
  mid=(b+a)/2 if b is not None and a is not None and a>=b else None
  spread_pct=((a-b)/mid) if mid and mid>0 else None
  rows.append({**m,"delta":delta,"iv":iv,"volume":bar.get("v") or 0,"spread_pct":spread_pct,
               "moneyness":m["strike"]/spot-1 if spot else None})
 out={}
 buckets={"dte_1_3":(1,3),"dte_4_7":(4,7),"dte_8_10":(8,10)}
 for name,(lo,hi) in buckets.items():
  sub=[r for r in rows if lo<=r["dte"]<=hi]
  for side in ("call","put"):
   ss=[r for r in sub if r["side"]==side]
   out[f"{name}_{side}_iv_med"]=_median([r["iv"] for r in ss])
   out[f"{name}_{side}_volume"]=sum(float(r["volume"] or 0) for r in ss)
  for target in (.25,.50):
   tag="25d" if target==.25 else "50d"
   for side in ("call","put"):
    ss=_delta_slice([r for r in sub if r["side"]==side],target)
    out[f"{name}_{side}_{tag}_iv"]=_median([r["iv"] for r in ss])
    out[f"{name}_{side}_{tag}_spread_pct"]=_median([r["spread_pct"] for r in ss])
    out[f"{name}_{side}_{tag}_n"]=len(ss)
   c=out.get(f"{name}_call_{tag}_iv");p=out.get(f"{name}_put_{tag}_iv")
   out[f"{name}_{tag}_put_minus_call_iv"]=(p-c) if p is not None and c is not None else None
 return out
