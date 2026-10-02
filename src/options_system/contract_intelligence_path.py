from .conditional_path_distribution import split_path_scenarios,mixture_path_weights
from .weighted_option_ev import weighted_option_ev
from .weighted_stress import weighted_stress_cube
def evaluate_contract_path_aware(contract,spot,development_scenarios,p_raw,p_calibrated,p_conservative,costs=0,iv_shifts=(-.03,0,.03),elapsed_day=3):
 event,non=split_path_scenarios(development_scenarios,.01)
 probs={"raw":p_raw,"calibrated":p_calibrated,"conservative":p_conservative};ev={}
 for name,p in probs.items():
  ev[name]=weighted_option_ev(contract,spot,mixture_path_weights(p,event,non),elapsed_days=elapsed_day,costs=costs)
 cw=mixture_path_weights(p_conservative,event,non)
 stress=weighted_stress_cube(contract,spot,cw,iv_shifts=iv_shifts,elapsed_days=(elapsed_day,),costs=costs)
 return {"option_type":contract.option_type,"strike":contract.strike,"dte":contract.dte,"premium":contract.premium,"iv":contract.iv,
 "sample_n":len(development_scenarios),"event_n":len(event),"non_event_n":len(non),"ev":ev,"stress":stress,
 "robust_positive_count":sum(x["expected_pnl"]>0 for x in stress),"stress_count":len(stress),
 "worst_stress_ev":min(x["expected_pnl"] for x in stress) if stress else None,"stress_elapsed_day":elapsed_day}
