from src.options_system.empirical_distribution import quantile,empirical_distribution,nearest_neighbors
def test_quantiles(): assert quantile([1,2,3,4],.5)==2.5
def test_distribution_probabilities():
 r=empirical_distribution([-.02,-.005,.01,.03]);assert r["n"]==4 and r["p_abs_1pct"]==.75 and r["p_up"]==.5
def test_neighbors_return_k():
 rows=[{"x":0},{"x":1},{"x":2}];assert [r["x"] for r in nearest_neighbors(rows,{"x":1.1},["x"],2)]==[1,2]
