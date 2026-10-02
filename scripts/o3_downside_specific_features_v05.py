import json
from options_system.env import load_local_env
from options_system.spy_daily import fetch_daily_spy
from options_system.downside_open_features import downside_open_features,DOWNSIDE_FEATURE_NAMES
from options_system.open_outcomes import open_outcome
from options_system.direction_model import fit_logistic,predict,brier,logloss
load_local_env();r=fetch_daily_spy("2018-11-01T00:00:00Z","2026-09-01T00:00:00Z");D=[]
for i in range(len(r)-2):
 f=downside_open_features(r,i)
 if f:
  y=1 if open_outcome(r,i,3)["mae"]<=-.01 else 0;D.append((r[i]["date"],f,y))
tr=[z for z in D if z[0]<="2021-12-31"];X=lambda z:[z[1][k] for k in DOWNSIDE_FEATURE_NAMES]
mu=[sum(X(z)[j] for z in tr)/len(tr) for j in range(len(DOWNSIDE_FEATURE_NAMES))];sd=[(sum((X(z)[j]-mu[j])**2 for z in tr)/(len(tr)-1))**.5 or 1 for j in range(len(mu))]
S=lambda z:[(X(z)[j]-mu[j])/sd[j] for j in range(len(mu))];yt=[z[2] for z in tr];w=fit_logistic([S(z) for z in tr],yt,steps=1400,lr=.025);base=sum(yt)/len(yt)
out={}
for label,a,b in (("2022","2022-01-01","2022-12-31"),("2023","2023-01-01","2023-12-31"),("validation","2022-01-01","2023-12-31"),("2024_diag","2024-01-01","2024-12-31"),("2025_diag","2025-01-01","2025-12-31"),("2026_diag","2026-01-01","2026-12-31")):
 ds=[z for z in D if a<=z[0]<=b];y=[z[2] for z in ds];p=predict(w,[S(z) for z in ds]);q=[base]*len(y)
 out[label]={"n":len(y),"event_rate":sum(y)/len(y),"mean_p":sum(p)/len(p),"delta_brier":brier(y,q)-brier(y,p),"delta_logloss":logloss(y,q)-logloss(y,p)}
open("artifacts/o3_downside_specific_features_v05.json","w").write(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
