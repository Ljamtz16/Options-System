import pytest
from src.options_system.direction_labels import open_direction_labels,expanding_baseline
def test_h3_open_terminal_is_t_plus_2():
 r=[{"date":"1","open":100,"close":101},{"date":"2","open":101,"close":102},{"date":"3","open":102,"close":103}]
 x=open_direction_labels(r,3)[0];assert x["terminal_return"]==pytest.approx(.03) and x["label_end"]=="3"
def test_baseline_uses_past_only():
 x=[{"date":str(i),"up":i%2} for i in range(5)];r=expanding_baseline(x,2);assert r[0]["baseline_p_up"]==.5
