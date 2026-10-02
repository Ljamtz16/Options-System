from src.options_system.option_simulator import OptionContract,scenario_value
from src.options_system.option_math import black_scholes
def test_simulator_matches_base_engine():
 c=OptionContract("call",100,10,3,0.2);a=scenario_value(c,101)
 b=black_scholes(101,100,10/365,0.04,.2,"call")["price"];assert abs(a-b)<1e-12
