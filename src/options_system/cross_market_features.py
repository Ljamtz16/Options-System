def _price(snapshot):
 t=(snapshot or {}).get("latestTrade") or {};q=(snapshot or {}).get("latestQuote") or {}
 p=t.get("p")
 if p:return float(p)
 b,a=q.get("bp"),q.get("ap")
 return (float(b)+float(a))/2 if b and a else None

def cross_market_features(spy,qqq,iwm):
 out={}
 for sym,s in (("spy",spy),("qqq",qqq),("iwm",iwm)):
  p=_price(s);d=s.get("dailyBar") or {};prev=s.get("prevDailyBar") or {}
  o=d.get("o");pc=prev.get("c")
  out[f"{sym}_price"]=p
  out[f"{sym}_from_open"]=(p/float(o)-1) if p and o else None
  out[f"{sym}_gap"]=(float(o)/float(pc)-1) if o and pc else None
 if out.get("spy_from_open") is not None and out.get("qqq_from_open") is not None:
  out["qqq_minus_spy_from_open"]=out["qqq_from_open"]-out["spy_from_open"]
 if out.get("spy_from_open") is not None and out.get("iwm_from_open") is not None:
  out["iwm_minus_spy_from_open"]=out["iwm_from_open"]-out["spy_from_open"]
 vals=[out.get("spy_from_open"),out.get("qqq_from_open"),out.get("iwm_from_open")]
 if all(v is not None for v in vals):
  out["cross_market_up_count"]=sum(v>0 for v in vals)
  out["cross_market_down_count"]=sum(v<0 for v in vals)
  out["cross_market_dispersion"]=max(vals)-min(vals)
 return out
