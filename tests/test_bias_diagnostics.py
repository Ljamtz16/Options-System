import pytest
from src.options_system.bias_diagnostics import return_diagnostics,center_returns,invert_returns
def test_center_zero_mean():assert sum(center_returns([1,2,3]))==pytest.approx(0)
def test_invert_swaps_direction():
 a=return_diagnostics([-.02,.03,.04]);b=return_diagnostics(invert_returns([-.02,.03,.04]));assert a["all"]["p_up"]==b["all"]["p_down"]
