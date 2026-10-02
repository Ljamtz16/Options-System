from src.options_system.probability_guardrail import wilson_interval,conservative_probability
def test_wilson_contains_rate():
 lo,hi=wilson_interval(60,100);assert lo<.6<hi
def test_guardrail_never_increases():
 assert conservative_probability(.8,.7,100)<=.8
def test_sparse_bin_caps_at_half():
 assert conservative_probability(.9,.8,5)==.5
