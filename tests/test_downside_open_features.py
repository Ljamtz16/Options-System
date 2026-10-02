import copy
from options_system.downside_open_features import downside_open_features
def rows(n=80):
 return [{"open":100+i,"high":102+i,"low":99+i,"close":101+i,"volume":1000+i} for i in range(n)]
def test_same_day_mutation_does_not_change_downside_features():
 r=rows();a=downside_open_features(r,65);q=copy.deepcopy(r);q[65].update(close=999,high=999,low=1);assert a==downside_open_features(q,65)
def test_future_mutation_does_not_change_downside_features():
 r=rows();a=downside_open_features(r,65);q=copy.deepcopy(r);q[70]["close"]=999;assert a==downside_open_features(q,65)
def test_current_open_changes_gap_only():
 r=rows();a=downside_open_features(r,65);q=copy.deepcopy(r);q[65]["open"]+=5;b=downside_open_features(q,65);assert {k for k in a if a[k]!=b[k]}=={"gap"}
