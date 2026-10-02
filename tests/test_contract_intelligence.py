from src.options_system.option_simulator import OptionContract
from src.options_system.contract_intelligence import evaluate_contract
def test_contract_evaluation_shape():
 c=OptionContract("call",100,7,2,.2);r=evaluate_contract(c,100,[-.03,-.005,.004,.02],.7,.65,.55,costs=1)
 assert set(r["ev"])=={"raw","calibrated","conservative"} and r["stress_count"]==9
def test_robust_count_bounded():
 c=OptionContract("put",100,7,2,.2);r=evaluate_contract(c,100,[-.03,.03],.7,.65,.55)
 assert 0<=r["robust_positive_count"]<=r["stress_count"]
