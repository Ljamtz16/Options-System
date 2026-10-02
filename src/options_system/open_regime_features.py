import math
def open_regime_features(rows,i):
 if i<61:return None
 prev=rows[:i];c=[float(x["close"]) for x in prev];h=[float(x["high"]) for x in prev];l=[float(x["low"]) for x in prev];v=[float(x["volume"]) for x in prev]
 op=float(rows[i]["open"]);pc=c[-1]
 rets=[c[k]/c[k-1]-1 for k in range(1,len(c))]
 def vol(n):
  a=rets[-n:];m=sum(a)/len(a);return (sum((x-m)**2 for x in a)/(len(a)-1))**.5
 tr=[max(h[k]-l[k],abs(h[k]-c[k-1]),abs(l[k]-c[k-1])) for k in range(max(1,len(c)-14),len(c))]
 hi60=max(c[-60:]);avgvol=sum(v[-20:])/20
 base={"ret1":c[-1]/c[-2]-1,"ret2":c[-1]/c[-3]-1,"ret5":c[-1]/c[-6]-1,"ret10":c[-1]/c[-11]-1,"ret20":c[-1]/c[-21]-1,"gap":op/pc-1}
 regime={"vol5":vol(5),"vol20":vol(20),"vol60":vol(60),"sma20":pc/(sum(c[-20:])/20)-1,"sma50":pc/(sum(c[-50:])/50)-1,
 "drawdown60":pc/hi60-1,"atr14":sum(tr)/len(tr)/pc,"prev_range":h[-1]/l[-1]-1,"prev_intraday":c[-1]/float(prev[-1]["open"])-1,
 "volume_ratio":v[-1]/avgvol if avgvol else 1}
 return base,regime
