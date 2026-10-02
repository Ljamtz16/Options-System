import copy,pytest
from src.options_system.spy_open_features import spy_open_features
from src.options_system.open_outcomes import open_outcome
def rows(n=80):
 return [{"date":f"2024-01-{i+1:02d}","open":100+i,"high":102+i,"low":99+i,"close":101+i,"volume":1000+i} for i in range(n)]
def test_same_day_close_high_low_volume_do_not_change_features():
 r=rows();a=spy_open_features(r,65);q=copy.deepcopy(r);q[65].update(close=999,high=999,low=1,volume=999999);assert a==spy_open_features(q,65)
def test_future_does_not_change_features():
 r=rows();a=spy_open_features(r,65);q=copy.deepcopy(r);q[70].update(close=999,high=999);assert a==spy_open_features(q,65)
def test_current_open_only_changes_open_and_gap():
 r=rows();a=spy_open_features(r,65);q=copy.deepcopy(r);q[65]["open"]+=5;b=spy_open_features(q,65)
 changed={k for k in a if a[k]!=b[k]};assert changed=={"open_t","gap"}
def test_metadata():
 x=spy_open_features(rows(),65);assert x["decision_time"]=="OPEN" and x["feature_asof_date"]=="2024-01-65"
def test_h3_is_t_through_t_plus_2():
 r=rows();x=open_outcome(r,10,3);assert x["label_end"]==r[12]["date"] and x["terminal_return"]==pytest.approx(float(r[12]["close"])/float(r[10]["open"])-1)
def test_h1_includes_current_session_high_low():
 r=rows();x=open_outcome(r,10,1);assert x["mfe"]==pytest.approx(r[10]["high"]/r[10]["open"]-1)
