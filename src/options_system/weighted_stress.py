from .option_simulator import scenario_pnl
def weighted_stress_cube(contract,spot,weighted_returns,iv_shifts=(-.03,0,.03),elapsed_days=(3,),risk_free=.04,costs=0):
 out=[]
 for days in elapsed_days:
  for shift in iv_shifts:
   ev=0.0;pp=0.0;ws=0.0
   for ret,w,group in weighted_returns:
    pnl=scenario_pnl(contract,spot*(1+ret),risk_free,max(1e-6,contract.iv+shift),max(0,contract.dte-days),costs/2,costs/2)["net_pnl"]
    ev+=pnl*w;pp+=w if pnl>0 else 0;ws+=w
   out.append({"elapsed_days":days,"iv_shift":shift,"weight_sum":ws,"expected_pnl":ev,"p_profit":pp})
 return out
