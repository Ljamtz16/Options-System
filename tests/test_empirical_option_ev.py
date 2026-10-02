from src.options_system.option_simulator import OptionContract
from src.options_system.empirical_option_ev import empirical_option_ev
def test_empirical_ev_count():
 c=OptionContract("call",100,7,2,.2);r=empirical_option_ev(c,100,[-.02,0,.02]);assert r["n"]==3
def test_call_larger_returns_help():
 c=OptionContract("call",100,7,2,.2);a=empirical_option_ev(c,100,[.01]);b=empirical_option_ev(c,100,[.03]);assert b["expected_pnl"]>a["expected_pnl"]
