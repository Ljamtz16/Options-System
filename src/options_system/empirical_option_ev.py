from .option_simulator import scenario_pnl
def empirical_option_ev(contract,spot,returns,elapsed_days=3,risk_free=.04,iv_shift=0,costs=0):
 vals=[]
 remain=max(0,contract.dte-elapsed_days);sigma=max(1e-6,contract.iv+iv_shift)
 for r in returns:
  if r is None:continue
  x=scenario_pnl(contract,spot*(1+float(r)),risk_free,sigma,remain,costs/2,costs/2)
  vals.append(x["net_pnl"])
 if not vals:return {"n":0,"expected_pnl":None}
 s=sorted(vals)
 def q(a):
  i=(len(s)-1)*a;lo=int(i);hi=min(lo+1,len(s)-1);w=i-lo;return s[lo]*(1-w)+s[hi]*w
 return {"n":len(vals),"expected_pnl":sum(vals)/len(vals),"p_profit":sum(x>0 for x in vals)/len(vals),
 "p_loss":sum(x<0 for x in vals)/len(vals),"pnl_q10":q(.1),"pnl_q50":q(.5),"pnl_q90":q(.9),
 "worst":min(vals),"best":max(vals)}
