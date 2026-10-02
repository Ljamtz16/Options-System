from .option_simulator import scenario_pnl
def weighted_option_ev(contract,spot,weighted_returns,elapsed_days=3,risk_free=.04,iv_shift=0,costs=0):
 rows=[];ev=0.0;wp=0.0
 for ret,w,group in weighted_returns:
  pnl=scenario_pnl(contract,spot*(1+ret),risk_free,max(1e-6,contract.iv+iv_shift),max(0,contract.dte-elapsed_days),costs/2,costs/2)["net_pnl"]
  rows.append((pnl,w,group));ev+=pnl*w;wp+=w
 return {"n":len(rows),"weight_sum":wp,"expected_pnl":ev,"p_profit":sum(w for pnl,w,_ in rows if pnl>0)}
