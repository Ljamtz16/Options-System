def return_diagnostics(returns,threshold=.01):
 r=[float(x) for x in returns if x is not None]
 e=[x for x in r if abs(x)>=threshold];n=[x for x in r if abs(x)<threshold]
 def s(x):
  return {"n":len(x),"mean":sum(x)/len(x) if x else None,"p_up":sum(v>0 for v in x)/len(x) if x else None,
  "p_down":sum(v<0 for v in x)/len(x) if x else None}
 return {"all":s(r),"event":s(e),"non_event":s(n)}
def center_returns(returns):
 r=[float(x) for x in returns];m=sum(r)/len(r);return [x-m for x in r]
def invert_returns(returns):return [-float(x) for x in returns]
