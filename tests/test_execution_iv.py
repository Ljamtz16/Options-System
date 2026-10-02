import pytest
from src.options_system.execution_model import ExecutionQuote,entry_price_long,exit_price_long,round_trip_execution_cost
from src.options_system.iv_scenarios import iv_scenarios
def test_long_fills_inside_spread():
 q=ExecutionQuote(1,1.2);assert 1.1<=entry_price_long(q)<=1.2 and 1<=exit_price_long(q)<=1.1
def test_execution_drag_positive():
 q=ExecutionQuote(1,1.2);assert round_trip_execution_cost(q,q)["execution_drag"]>0
def test_invalid_quote_rejected():
 with pytest.raises(ValueError):entry_price_long(ExecutionQuote(1,0))
def test_iv_scenarios_ordered():
 s=iv_scenarios(.2,.03);assert s["crush"]<s["unchanged"]<s["expansion"]
