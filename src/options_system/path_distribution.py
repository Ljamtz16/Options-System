def path_metrics(open_price,highs,lows,closes):
 if open_price<=0:raise ValueError("open_price")
 if not highs or len(highs)!=len(lows) or len(highs)!=len(closes):raise ValueError("path")
 mfe=max(float(x)/open_price-1 for x in highs)
 mae=min(float(x)/open_price-1 for x in lows)
 terminal=float(closes[-1])/open_price-1
 return {"mfe":mfe,"mae":mae,"terminal_return":terminal}
def barrier_touch(open_price,highs,lows,up=.01,down=.01):
 u=open_price*(1+up);d=open_price*(1-down)
 for i,(h,l) in enumerate(zip(highs,lows)):
  hu=float(h)>=u;ld=float(l)<=d
  if hu and ld:return {"label":"AMBIGUOUS_SAME_SESSION","session_offset":i}
  if hu:return {"label":"UP","session_offset":i}
  if ld:return {"label":"DOWN","session_offset":i}
 return {"label":"NEITHER","session_offset":None}
