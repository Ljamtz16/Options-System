from .option_simulator import OptionContract
from .contract_intelligence_path import evaluate_contract_path_aware
from .contract_quality import quality_flags
def evaluate_synthetic_chain_path(chain,spot,development_scenarios,p_raw,p_calibrated,p_conservative,slippage_fraction=.25,fees=0):
 out=[]
 for x in chain:
  spread=x["ask"]-x["bid"];entry=min(x["ask"],x["mid"]+spread*slippage_fraction)
  drag=(entry-x["mid"])*100+fees
  c=OptionContract(x["option_type"],x["strike"],x["dte"],entry,x["iv"])
  card=evaluate_contract_path_aware(c,spot,development_scenarios,p_raw,p_calibrated,p_conservative,costs=drag)
  card.update({"symbol":x["symbol"],"source":"SIMULATED","bid":x["bid"],"ask":x["ask"],"entry_fill":entry,"execution_drag":drag})
  card["quality_flags"]=quality_flags({**card,"sample_n":len(development_scenarios)})
  out.append(card)
 return out
