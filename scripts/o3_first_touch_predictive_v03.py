import json
from options_system.env import load_local_env
from options_system.spy_daily import fetch_daily_spy
from options_system.open_first_touch import label_family
from options_system.open_regime_features import open_regime_features
from options_system.direction_model import fit_logistic,predict,brier,logloss
load_local_env();r=fetch_daily_spy("2018-11-01T00:00:00Z","2026-09-01T00:00:00Z");names=["sym_05","up10_dn05","up05_dn10","sym_10"];allrows={k:[] for k in names}
for i in range(len(r)-2):
 z=open_regime_features(r,i)
 if not z:continue
 b,g=z;x=list(b.values())+list(g.values())
 for k,v in label_family(r,i).items():allrows[k].append((r[i]["date"],x,v["label"]))
out={}
for k,data in allrows.items():
 tr=[z for z in data if z[0]<="2021-12-31" and z[2] in ("UP","DOWN")];va_all=[z for z in data if "2022-01-01"<=z[0]<="2023-12-31"];va=[z for z in va_all if z[2] in ("UP","DOWN")]
 mu=[sum(z[1][j] for z in tr)/len(tr) for j in range(len(tr[0][1]))];sd=[(sum((z[1][j]-mu[j])**2 for z in tr)/(len(tr)-1))**.5 or 1 for j in range(len(mu))]
 S=lambda z:[(z[1][j]-mu[j])/sd[j] for j in range(len(mu))];ytr=[1 if z[2]=="UP" else 0 for z in tr];w=fit_logistic([S(z) for z in tr],ytr,steps=1500,lr=.03)
 y=[1 if z[2]=="UP" else 0 for z in va];p=predict(w,[S(z) for z in va]);base=sum(ytr)/len(ytr);q=[base]*len(y)
 out[k]={"train_resolved_n":len(tr),"validation_total_n":len(va_all),"validation_resolved_n":len(va),"validation_resolved_coverage":len(va)/len(va_all),
 "train_p_up_resolved":base,"validation_p_up_resolved":sum(y)/len(y),"mean_model_p_up":sum(p)/len(p),
 "delta_brier":brier(y,q)-brier(y,p),"delta_logloss":logloss(y,q)-logloss(y,p)}
open("artifacts/o3_first_touch_predictive_v03.json","w").write(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
