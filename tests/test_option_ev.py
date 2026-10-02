from src.options_system.option_ev import magnitude_ev,conservative_magnitude_ev
def test_magnitude_is_direction_neutral():
 r=magnitude_ev(.8,100,-50,-20);assert r["p_up"]==r["p_down"]==.4
def test_probabilities_sum_one():
 r=magnitude_ev(.7,1,1,0);assert abs(r["p_up"]+r["p_down"]+r["p_flat"]-1)<1e-12
def test_three_probability_views():
 r=conservative_magnitude_ev(.8,.75,.65,100,-50,-20);assert set(r)=={"raw","calibrated","conservative"}
