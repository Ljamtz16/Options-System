from src.options_system.open_regime_features import open_regime_features
def rows(n=70):
 return [{"open":100+i,"high":102+i,"low":99+i,"close":101+i,"volume":1000+i} for i in range(n)]
def test_current_close_mutation_does_not_change_features():
 r=rows();a=open_regime_features(r,65);r[65]["close"]=999;b=open_regime_features(r,65);assert a==b
def test_future_mutation_does_not_change_features():
 r=rows();a=open_regime_features(r,65);r[66]["high"]=999;b=open_regime_features(r,65);assert a==b
def test_current_open_changes_gap_only():
 r=rows();a=open_regime_features(r,65);r[65]["open"]+=5;b=open_regime_features(r,65);assert a[1]==b[1] and a[0]["gap"]!=b[0]["gap"]
