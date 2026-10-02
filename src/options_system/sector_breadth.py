SECTORS=("XLK","XLF","XLE","XLV","XLI")
def _ret_from_open(s):
 t=(s or {}).get("latestTrade") or {};d=(s or {}).get("dailyBar") or {}
 p=t.get("p");o=d.get("o")
 return float(p)/float(o)-1 if p and o else None
def sector_breadth_features(snaps):
 out={};vals=[]
 for sym in SECTORS:
  r=_ret_from_open(snaps.get(sym) or {})
  out[f"{sym.lower()}_from_open"]=r
  if r is not None:vals.append(r)
 out["sector_count"]=len(vals)
 out["sector_up_count"]=sum(v>0 for v in vals)
 out["sector_down_count"]=sum(v<0 for v in vals)
 out["sector_mean_from_open"]=sum(vals)/len(vals) if vals else None
 out["sector_dispersion"]=max(vals)-min(vals) if vals else None
 return out
