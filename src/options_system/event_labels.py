def first_touch(future_returns,upper,lower):
    up=next((i+1 for i,x in enumerate(future_returns) if x>=upper),None)
    dn=next((i+1 for i,x in enumerate(future_returns) if x<=lower),None)
    if up is None and dn is None:return "NEITHER"
    if dn is None or (up is not None and up<dn):return "UP"
    if up is None or dn<up:return "DOWN"
    return "SAME_SESSION"

def event_labels(closes,horizons=(1,3,5,10)):
    out=[]
    for i,(d,c0) in enumerate(closes):
        z={"date":d}
        for h in horizons:
            future=[float(x[1])/float(c0)-1 for x in closes[i+1:i+1+h]]
            complete=i+h<len(closes)
            z[f"abs_gt_1pct_h{h}"]=(max((abs(x) for x in future),default=0)>=.01) if complete else None
            z[f"up05_dn05_h{h}"]=first_touch(future,.005,-.005) if complete else None
            z[f"up10_dn05_h{h}"]=first_touch(future,.01,-.005) if complete else None
            z[f"up05_dn10_h{h}"]=first_touch(future,.005,-.01) if complete else None
        out.append(z)
    return out
