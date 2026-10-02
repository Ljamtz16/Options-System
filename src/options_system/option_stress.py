from .option_simulator import scenario_pnl
def stress_cube(contract,spot,returns,iv_shifts=(-.03,0,.03),elapsed_days=(1,2,3),risk_free=.04,costs=0):
 out=[]
 for days in elapsed_days:
  for shift in iv_shifts:
   pnls=[scenario_pnl(contract,spot*(1+r),risk_free,max(1e-6,contract.iv+shift),max(0,contract.dte-days),costs/2,costs/2)["net_pnl"] for r in returns]
   if pnls:out.append({"elapsed_days":days,"iv_shift":shift,"n":len(pnls),"expected_pnl":sum(pnls)/len(pnls),"p_profit":sum(x>0 for x in pnls)/len(pnls),"worst":min(pnls),"best":max(pnls)})
 return out
