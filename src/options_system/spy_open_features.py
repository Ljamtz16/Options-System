def spy_open_features(rows,i):
 if i<61:return None
 prev=rows[:i];c=[float(x["close"]) for x in prev];h=[float(x["high"]) for x in prev];l=[float(x["low"]) for x in prev];v=[float(x["volume"]) for x in prev]
 op=float(rows[i]["open"]);pc=c[-1];rets=[c[k]/c[k-1]-1 for k in range(1,len(c))]
 def vol(n):
  a=rets[-n:];m=sum(a)/len(a);return (sum((x-m)**2 for x in a)/(len(a)-1))**.5
 tr=[max(h[k]-l[k],abs(h[k]-c[k-1]),abs(l[k]-c[k-1])) for k in range(max(1,len(c)-14),len(c))]
 avgv=sum(v[-20:])/20
 return {"decision_date":rows[i]["date"],"decision_time":"OPEN","feature_asof_date":rows[i-1]["date"],
 "open_t":op,"ret_1":c[-1]/c[-2]-1,"ret_2":c[-1]/c[-3]-1,"ret_5":c[-1]/c[-6]-1,"ret_10":c[-1]/c[-11]-1,"ret_20":c[-1]/c[-21]-1,"ret_60":c[-1]/c[-61]-1,
 "gap":op/pc-1,"prev_intraday":c[-1]/float(prev[-1]["open"])-1,"prev_range":h[-1]/l[-1]-1,"atr_14":sum(tr)/len(tr)/pc,
 "vol_5":vol(5),"vol_20":vol(20),"vol_60":vol(60),"close_sma20":pc/(sum(c[-20:])/20)-1,"close_sma50":pc/(sum(c[-50:])/50)-1,
 "drawdown_60":pc/max(c[-60:])-1,"volume_ratio":v[-1]/avgv if avgv else 1}
FEATURE_NAMES=["ret_1","ret_2","ret_5","ret_10","ret_20","ret_60","gap","prev_intraday","prev_range","atr_14","vol_5","vol_20","vol_60","close_sma20","close_sma50","drawdown_60","volume_ratio"]
