from .option_simulator import OptionContract
from .conditional_distribution import conditional_samples,mixture_weights
from .weighted_option_ev import weighted_option_ev
from .option_stress import stress_cube
def evaluate_contract(contract,spot,development_returns,p_raw,p_calibrated,p_conservative,costs=0,iv_shifts=(-.03,0,.03),elapsed_days=(1,2,3)):
 event,non=conditional_samples(development_returns,.01)
 probs={"raw":p_raw,"calibrated":p_calibrated,"conservative":p_conservative}
 ev={}
 for name,p in probs.items():
  w=mixture_weights(p,event,non)
  ev[name]=weighted_option_ev(contract,spot,w,elapsed_days=3,costs=costs)
 stress=stress_cube(contract,spot,development_returns,iv_shifts=iv_shifts,elapsed_days=elapsed_days,costs=costs)
 return {"option_type":contract.option_type,"strike":contract.strike,"dte":contract.dte,
 "premium":contract.premium,"iv":contract.iv,"moneyness":contract.strike/spot-1,
 "sample_n":len(development_returns),"event_n":len(event),"non_event_n":len(non),
 "ev":ev,"stress":stress,
 "robust_positive_count":sum(x["expected_pnl"]>0 for x in stress),
 "stress_count":len(stress),"worst_stress_ev":min(x["expected_pnl"] for x in stress) if stress else None}
