from options_system.drift_neutral import center_terminal_returns,directional_tilt_weights
from options_system.research_decision_engine import research_decision
def test_center_removes_mean():
 s=[{"terminal_return":.02},{"terminal_return":0.0}]
 x=center_terminal_returns(s);assert abs(sum(z["terminal_return"] for z in x)/len(x))<1e-12
def test_tilt_can_favor_down():
 w=directional_tilt_weights([-.02,-.01,.01,.02],.4);assert abs(sum(x[1] for x in w if x[2]=="DOWN")-.6)<1e-12
def test_no_direction_means_no_trade():
 assert research_decision(True,False,"NONE",0)["decision"]=="NO_TRADE_DIRECTION"
def test_valid_down_becomes_put_candidate():
 x=research_decision(True,True,"DOWN",-.06,True,12,True,True);assert x["decision"]=="RESEARCH_PUT_CANDIDATE"
