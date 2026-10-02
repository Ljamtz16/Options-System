from copy import deepcopy
from src.options_system.spy_features import build_features,FEATURES
def rows(n=80):
 return [{"date":str(i),"open":100+i,"high":102+i,"low":99+i,"close":101+i,"volume":1000+i} for i in range(n)]
def test_future_invariance():
 a=rows(); x=build_features(a)[65]
 b=deepcopy(a); b[66]["close"]=9999; b[70]["volume"]=999999
 y=build_features(b)[65]
 assert all(x[k]==y[k] for k in FEATURES)
def test_contract_has_18_features(): assert len(FEATURES)==18
