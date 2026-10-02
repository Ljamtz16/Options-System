def downside_open_features(rows,i):
 if i<61:return None
 prev=rows[:i];c=[float(x["close"]) for x in prev];o=[float(x["open"]) for x in prev];h=[float(x["high"]) for x in prev];l=[float(x["low"]) for x in prev]
 ret=[c[k]/c[k-1]-1 for k in range(1,len(c))];op=float(rows[i]["open"]);pc=c[-1]
 def frac_neg(n):a=ret[-n:];return sum(x<0 for x in a)/len(a)
 def downside_vol(n):
  a=[min(0,x) for x in ret[-n:]];return (sum(x*x for x in a)/len(a))**.5
 streak=0
 for x in reversed(ret):
  if x<0:streak+=1
  else:break
 return {"gap":op/pc-1,"ret1":ret[-1],"ret2":c[-1]/c[-3]-1,"ret5":c[-1]/c[-6]-1,"ret10":c[-1]/c[-11]-1,
 "neg_frac5":frac_neg(5),"neg_frac10":frac_neg(10),"neg_frac20":frac_neg(20),
 "downvol5":downside_vol(5),"downvol20":downside_vol(20),"downvol60":downside_vol(60),
 "down_streak":streak,"drawdown20":pc/max(c[-20:])-1,"drawdown60":pc/max(c[-60:])-1,
 "prev_intraday":c[-1]/o[-1]-1,"prev_range":h[-1]/l[-1]-1,
 "below_sma20":pc/(sum(c[-20:])/20)-1,"below_sma50":pc/(sum(c[-50:])/50)-1}
DOWNSIDE_FEATURE_NAMES=["gap","ret1","ret2","ret5","ret10","neg_frac5","neg_frac10","neg_frac20","downvol5","downvol20","downvol60","down_streak","drawdown20","drawdown60","prev_intraday","prev_range","below_sma20","below_sma50"]
