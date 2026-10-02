from src.options_system.option_simulator import OptionContract,scenario_value,scenario_pnl,symmetric_move_scenarios
def test_expiry_intrinsic():
 c=OptionContract("call",100,0,2,0.2);assert scenario_value(c,110)==10
def test_call_upside_beats_downside():
 c=OptionContract("call",100,10,3,0.2);s=symmetric_move_scenarios(c,100);assert s["up"]["net_pnl"]>s["down"]["net_pnl"]
def test_put_downside_beats_upside():
 c=OptionContract("put",100,10,3,0.2);s=symmetric_move_scenarios(c,100);assert s["down"]["net_pnl"]>s["up"]["net_pnl"]
def test_costs_reduce_pnl():
 c=OptionContract("call",100,10,3,0.2);a=scenario_pnl(c,101,dte=7);b=scenario_pnl(c,101,dte=7,entry_cost=1,exit_cost=2);assert round(a["net_pnl"]-b["net_pnl"],8)==3
