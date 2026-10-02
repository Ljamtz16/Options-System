from dataclasses import dataclass
from .option_math import black_scholes
@dataclass(frozen=True)
class OptionContract:
 option_type:str; strike:float; dte:float; premium:float; iv:float; multiplier:int=100
def scenario_value(contract,spot,risk_free=0.04,iv=None,dte=None):
 sigma=contract.iv if iv is None else iv;days=contract.dte if dte is None else max(0.0,dte)
 if days<=0:
  return max(0.0,spot-contract.strike) if contract.option_type=="call" else max(0.0,contract.strike-spot)
 return black_scholes(spot,contract.strike,days/365.0,risk_free,sigma,contract.option_type)["price"]
def scenario_pnl(contract,spot,risk_free=0.04,iv=None,dte=None,entry_cost=0.0,exit_cost=0.0):
 value=scenario_value(contract,spot,risk_free,iv,dte);gross=(value-contract.premium)*contract.multiplier
 return {"option_value":value,"gross_pnl":gross,"net_pnl":gross-entry_cost-exit_cost}
def symmetric_move_scenarios(contract,spot,move_pct=0.01,elapsed_days=3,risk_free=0.04,iv_shift=0.0,costs=0.0):
 remain=max(0.0,contract.dte-elapsed_days);sigma=max(1e-6,contract.iv+iv_shift)
 return {"up":scenario_pnl(contract,spot*(1+move_pct),risk_free,sigma,remain,costs/2,costs/2),
 "down":scenario_pnl(contract,spot*(1-move_pct),risk_free,sigma,remain,costs/2,costs/2),
 "flat":scenario_pnl(contract,spot,risk_free,sigma,remain,costs/2,costs/2)}
