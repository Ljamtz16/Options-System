import csv
from datetime import date,timedelta
def forward_returns(closes,horizons=(1,3,5,10)):
    rows=[]
    for i,(d,c) in enumerate(closes):
        r={"date":d,"close":float(c)}
        for h in horizons:
            r[f"ret_h{h}"]=float(closes[i+h][1])/float(c)-1 if i+h<len(closes) else None
        rows.append(r)
    return rows
def path_outcomes(closes,horizon=10,up=.005,down=.005):
    out=[]
    for i,(d,c0) in enumerate(closes):
        future=[float(x[1])/float(c0)-1 for x in closes[i+1:i+1+horizon]]
        up_i=next((j+1 for j,x in enumerate(future) if x>=up),None)
        dn_i=next((j+1 for j,x in enumerate(future) if x<=-down),None)
        out.append({"date":d,"mfe":max(future) if future else None,"mae":min(future) if future else None,
          "up_before_down":None if not future else (up_i is not None and (dn_i is None or up_i<dn_i)),
          "down_before_up":None if not future else (dn_i is not None and (up_i is None or dn_i<up_i))})
    return out
