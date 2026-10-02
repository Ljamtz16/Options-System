import csv,json
from options_system.direction_model import fit_logistic,predict,brier,logloss
from options_system.spy_open_features import FEATURE_NAMES
D=list(csv.DictReader(open("data/processed/o2_open/spy_open_outcomes_v02.csv")))
def target(z,h):return 1 if max(float(z[f"mfe_h{h}"]),-float(z[f"mae_h{h}"]))>=.01 else 0
tr=[z for z in D if z["decision_date"]<="2021-12-31"];X=lambda z:[float(z[k]) for k in FEATURE_NAMES];mu=[sum(X(z)[j] for z in tr)/len(tr) for j in range(len(FEATURE_NAMES))];sd=[(sum((X(z)[j]-mu[j])**2 for z in tr)/(len(tr)-1))**.5 or 1 for j in range(len(mu))];S=lambda z:[(X(z)[j]-mu[j])/sd[j] for j in range(len(mu))]
out={}
for h in (1,3):
 yt=[target(z,h) for z in tr];w=fit_logistic([S(z) for z in tr],yt,steps=1200,lr=.03);base=sum(yt)/len(yt);out[f"path_abs_1pct_h{h}"]={}
 for label,a,b in (("2022","2022-01-01","2022-12-31"),("2023","2023-01-01","2023-12-31"),("2024_diag","2024-01-01","2024-12-31"),("2025_diag","2025-01-01","2025-12-31"),("2026_diag","2026-01-01","2026-12-31")):
  ds=[z for z in D if a<=z["decision_date"]<=b and z[f"label_end_h{h}"]];y=[target(z,h) for z in ds];p=predict(w,[S(z) for z in ds]);q=[base]*len(y)
  out[f"path_abs_1pct_h{h}"][label]={"n":len(y),"rate":sum(y)/len(y),"mean_p":sum(p)/len(p),"delta_brier":brier(y,q)-brier(y,p),"delta_logloss":logloss(y,q)-logloss(y,p)}
open("artifacts/o2_open_stability_v02.json","w").write(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
