import math
def quantile(values,q):
 x=sorted(values)
 if not x:return None
 pos=(len(x)-1)*q;lo=int(math.floor(pos));hi=int(math.ceil(pos))
 if lo==hi:return x[lo]
 return x[lo]*(hi-pos)+x[hi]*(pos-lo)
def empirical_distribution(returns,mfe=None,mae=None):
 r=[float(x) for x in returns if x is not None]
 if not r:return {"n":0}
 out={"n":len(r),"mean":sum(r)/len(r),"p_up":sum(x>0 for x in r)/len(r),
 "p_down":sum(x<0 for x in r)/len(r),"p_abs_1pct":sum(abs(x)>=.01 for x in r)/len(r),
 "quantiles":{str(q):quantile(r,q) for q in (.05,.10,.25,.50,.75,.90,.95)}}
 if mfe is not None:
  a=[float(x) for x in mfe if x is not None];out["mfe_quantiles"]={str(q):quantile(a,q) for q in (.1,.5,.9)}
 if mae is not None:
  a=[float(x) for x in mae if x is not None];out["mae_quantiles"]={str(q):quantile(a,q) for q in (.1,.5,.9)}
 return out
def nearest_neighbors(train_rows,current,features,k=100):
 scored=[]
 for r in train_rows:
  if any(r.get(f) is None or current.get(f) is None for f in features):continue
  d=math.sqrt(sum((float(r[f])-float(current[f]))**2 for f in features))
  scored.append((d,r))
 return [r for _,r in sorted(scored,key=lambda z:z[0])[:k]]
