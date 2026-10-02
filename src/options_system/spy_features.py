import math

FEATURES=("ret_1","ret_2","ret_5","ret_10","ret_20","ret_60","gap","intraday","range","atr_14",
"vol_5","vol_20","vol_60","vol_ratio","close_sma20","close_sma50","drawdown_60","volume_ratio")

def mean(x): return sum(x)/len(x) if x else None
def stdev(x):
    if len(x)<2:return None
    m=mean(x);return math.sqrt(sum((v-m)**2 for v in x)/(len(x)-1))
def build_features(rows):
    out=[]
    for i,r in enumerate(rows):
        c=float(r["close"]); prev=float(rows[i-1]["close"]) if i else None
        x={"date":r["date"]}
        for h in (1,2,5,10,20,60):
            x[f"ret_{h}"]=c/float(rows[i-h]["close"])-1 if i>=h else None
        x["gap"]=float(r["open"])/prev-1 if prev else None
        x["intraday"]=c/float(r["open"])-1
        x["range"]=(float(r["high"])-float(r["low"]))/c
        tr=[]
        for j in range(max(0,i-13),i+1):
            pc=float(rows[j-1]["close"]) if j else float(rows[j]["open"])
            tr.append(max(float(rows[j]["high"])-float(rows[j]["low"]),abs(float(rows[j]["high"])-pc),abs(float(rows[j]["low"])-pc)))
        x["atr_14"]=mean(tr)/c if i>=13 else None
        daily=[float(rows[j]["close"])/float(rows[j-1]["close"])-1 for j in range(1,i+1)]
        for w in (5,20,60): x[f"vol_{w}"]=stdev(daily[-w:]) if len(daily)>=w else None
        x["vol_ratio"]=x["vol_5"]/x["vol_20"] if x["vol_5"] is not None and x["vol_20"] else None
        x["close_sma20"]=c/mean([float(z["close"]) for z in rows[i-19:i+1]])-1 if i>=19 else None
        x["close_sma50"]=c/mean([float(z["close"]) for z in rows[i-49:i+1]])-1 if i>=49 else None
        hi=max(float(z["close"]) for z in rows[max(0,i-59):i+1]); x["drawdown_60"]=c/hi-1 if i>=59 else None
        av=mean([float(z["volume"]) for z in rows[i-19:i+1]]) if i>=19 else None
        x["volume_ratio"]=float(r["volume"])/av if av else None
        out.append(x)
    return out
