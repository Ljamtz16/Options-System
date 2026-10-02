import json
from options_system.env import load_local_env
from options_system.spy_daily import fetch_daily_spy
from options_system.open_first_touch import label_family
from options_system.open_regime_features import open_regime_features
from options_system.direction_model import fit_logistic,predict,brier,logloss
load_local_env();r=fetch_daily_spy("2018-11-01T00:00:00Z","2026-09-01T00:00:00Z");families=("sym_05","up10_dn05","up05_dn10","sym_10");D={k:[] for k in families}
for i in range(len(r)-2):
 z=open_regime_features(r,i)
 if not z:continue
 b,g=z;x=list(b.values())+list(g.values())
 for k,v in label_family(r,i).items():D[k].append((r[i]["date"],x,v["label"]))
out={}
for fam,data in D.items():
 out[fam]={}
 for target in ("UP","DOWN","NEITHER","AMBIGUOUS_SAME_SESSION"):
  tr=[z for z in data if z[0]<="2021-12-31"];va=[z for z in data if "2022-01-01"<=z[0]<="2023-12-31"]
  mu=[sum(z[1][j] for z in tr)/len(tr) for j in range(len(tr[0][1]))];sd=[(sum((z[1][j]-mu[j])**2 for z in tr)/(len(tr)-1))**.5 or 1 for j in range(len(mu))]
  S=lambda z:[(z[1][j]-mu[j])/sd[j] for j in range(len(mu))];yt=[1 if z[2]==target else 0 for z in tr];y=[1 if z[2]==target else 0 for z in va];w=fit_logistic([S(z) for z in tr],yt,steps=1000,lr=.025)
  p=predict(w,[S(z) for z in va]);base=sum(yt)/len(yt);q=[base]*len(y)
  out[fam][target]={"train_rate":base,"validation_rate":sum(y)/len(y),"mean_p":sum(p)/len(p),"delta_brier":brier(y,q)-brier(y,p),"delta_logloss":logloss(y,q)-logloss(y,p)}
open("artifacts/o3_first_touch_absolute_events_v03.json","w").write(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
