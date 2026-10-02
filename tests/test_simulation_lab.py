from src.options_system.synthetic_chain import synthetic_chain
from src.options_system.simulation_lab import evaluate_synthetic_chain
def test_lab_evaluates_all():
 c=synthetic_chain(100,dtes=(5,),moneyness=(0,));r=evaluate_synthetic_chain(c,100,[-.03,-.02,-.005,.004,.02,.03]*20,.7,.65,.55)
 assert len(r)==2 and all(x["source"]=="SIMULATED" for x in r)
def test_execution_drag_nonnegative():
 c=synthetic_chain(100,dtes=(5,),moneyness=(0,));r=evaluate_synthetic_chain(c,100,[-.02,.02]*60,.7,.65,.55)
 assert all(x["execution_drag"]>=0 for x in r)
