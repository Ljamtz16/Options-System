from src.options_system.option_simulator import OptionContract
from src.options_system.option_stress import stress_cube
def test_stress_cube_dimensions():
 c=OptionContract("call",100,7,2,.2);r=stress_cube(c,100,[-.02,.02]);assert len(r)==9
def test_iv_expansion_helps_long_option_same_time():
 c=OptionContract("call",100,7,2,.2);r=stress_cube(c,100,[0],elapsed_days=(2,));assert r[2]["expected_pnl"]>r[0]["expected_pnl"]
