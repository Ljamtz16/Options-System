from .option_simulator import OptionContract
from .contract_intelligence import evaluate_contract
from .contract_quality import quality_flags
def evaluate_synthetic_chain(chain,spot,development_returns,p_raw,p_calibrated,p_conservative,slippage_fraction=.25,fees=0):
 out=[]
 for x in chain:
  spread=x["ask"]-x["bid"];entry=min(x["ask"],x["mid"]+spread*slippage_fraction)
  execution_drag=(entry-x["mid"])*100+fees
  c=OptionContract(x["option_type"],x["strike"],x["dte"],entry,x["iv"])
  card=evaluate_contract(c,spot,development_returns,p_raw,p_calibrated,p_conservative,costs=execution_drag)
  card.update({"symbol":x["symbol"],"source":"SIMULATED","bid":x["bid"],"ask":x["ask"],"entry_fill":entry,"execution_drag":execution_drag})
  card["quality_flags"]=quality_flags({**card,"sample_n":len(development_returns)})
  out.append(card)
 return out
