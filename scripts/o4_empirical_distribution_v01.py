import json,math
from options_system.env import load_local_env
from options_system.spy_daily import fetch_daily_spy
from options_system.spy_features import build_features,FEATURES
from options_system.outcomes import forward_returns
from options_system.probability_baseline import fit_standardizer
from options_system.empirical_distribution import empirical_distribution
load_local_env();rows=fetch_daily_spy("2018-11-01T00:00:00Z","2026-09-01T00:00:00Z");feat=build_features(rows);ret=forward_returns([(r["date"],r["close"]) for r in rows])
data=[]
for i,r in enumerate(rows):
 x={**r,**feat[i],**ret[i]}
 if all(x.get(f) is not None for f in FEATURES) and x.get("ret_h3") is not None:data.append(x)
train=[r for r in data if r["date"]<="2021-12-31"];oos=[r for r in data if r["date"]>="2024-01-01"]
mu,sd=fit_standardizer([[float(r[f]) for f in FEATURES] for r in train])
def z(r):return [(float(r[f])-mu[j])/sd[j] for j,f in enumerate(FEATURES)]
tz=[z(r) for r in train];tr=[float(r["ret_h3"]) for r in train]
pred=[];actual=[]
for r in oos:
 q=z(r);idx=sorted(range(len(train)),key=lambda i:sum((tz[i][j]-q[j])**2 for j in range(len(q))))[:100]
 rr=[tr[i] for i in idx];pred.append(sum(rr)/len(rr));actual.append(float(r["ret_h3"]))
mae=sum(abs(pred[i]-actual[i]) for i in range(len(actual)))/len(actual);base=sum(tr)/len(tr);base_mae=sum(abs(base-x) for x in actual)/len(actual)
last=oos[-1];q=z(last);idx=sorted(range(len(train)),key=lambda i:sum((tz[i][j]-q[j])**2 for j in range(len(q))))[:100]
dist=empirical_distribution([tr[i] for i in idx])
out={"k":100,"train_n":len(train),"oos_n":len(oos),"oos_mean_return_mae_neighbors":mae,"oos_mean_return_mae_global_train":base_mae,"last_oos_date":last["date"],"last_oos_neighbor_distribution":dist}
open("artifacts/o4_empirical_distribution_v01.json","w").write(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
