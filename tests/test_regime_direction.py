from src.options_system.regime_direction import fit_regime_table,predict_regime
def test_unseen_regime_falls_back_to_global():
 m=fit_regime_table([{"regime":("A",),"up":1},{"regime":("B",),"up":0}]);assert predict_regime(m,("X",))==.5
def test_shrinkage_prevents_extreme_small_bin():
 m=fit_regime_table([{"regime":("A",),"up":1},{"regime":("B",),"up":0}],alpha=40);assert .5<predict_regime(m,("A",))<.6
