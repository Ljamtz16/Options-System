import csv,json
from options_system.direction_model import fit_logistic,predict,brier,logloss
from options_system.spy_open_features import FEATURE_NAMES
D=list(csv.DictReader(open("data/processed/o2_open/spy_open_outcomes_v02.csv")))
targets=[]
for h in (1,3,5,10):
 for th in (.005,.01):
  targets.append((f"terminal_abs_{int(th*1000):02d}bp_h{h}",h,th,"terminal"))
  targets.append((f"path_abs_{int(th*1000):02d}bp_h{h}",h,th,"path"))
def yval(z,h,th,kind):
 if not z[f"label_end_h{h}"]:return None
 if kind=="terminal":return 1 if abs(float(z[f"terminal_h{h}"]))>=th else 0
 return 1 if max(float(z[f"mfe_h{h}"]),-float(z[f"mae_h{h}"]))>=th else 0
out={}
for name,h,th,kind in targets:
 rows=[z for z in D if yval(z,h,th,kind) is not None];tr=[z for z in rows if z["decision_date"]<="2021-12-31"];va=[z for z in rows if "2022-01-01"<=z["decision_date"]<="2023-12-31"]
 X=lambda z:[float(z[k]) for k in FEATURE_NAMES];mu=[sum(X(z)[j] for z in tr)/len(tr) for j in range(len(FEATURE_NAMES))];sd=[(sum((X(z)[j]-mu[j])**2 for z in tr)/(len(tr)-1))**.5 or 1 for j in range(len(mu))]
 S=lambda z:[(X(z)[j]-mu[j])/sd[j] for j in range(len(mu))];yt=[yval(z,h,th,kind) for z in tr];yv=[yval(z,h,th,kind) for z in va];w=fit_logistic([S(z) for z in tr],yt,steps=1200,lr=.03);p=predict(w,[S(z) for z in va]);base=sum(yt)/len(yt);q=[base]*len(yv)
 out[name]={"train_n":len(tr),"validation_n":len(va),"train_rate":base,"validation_rate":sum(yv)/len(yv),"mean_model_p":sum(p)/len(p),"delta_brier":brier(yv,q)-brier(yv,p),"delta_logloss":logloss(yv,q)-logloss(yv,p)}
open("artifacts/o2_open_target_sweep_v02.json","w").write(json.dumps(out,indent=2))
print(json.dumps(dict(sorted(out.items(),key=lambda kv:kv[1]["delta_brier"],reverse=True)),indent=2))
