import csv,json
from options_system.direction_model import fit_logistic,predict,brier,logloss
from options_system.spy_open_features import FEATURE_NAMES
from options_system.open_probability_runtime import load_probability_artifact,score_open_features
D=list(csv.DictReader(open("data/processed/o2_open/spy_open_outcomes_v02.csv")))
A=load_probability_artifact("artifacts/o3/O3_OPEN_PATH_H3_PROB_V02.json")
def y(z):return 1 if float(z["mae_h3"])<=-.01 else 0
tr=[z for z in D if z["decision_date"]<="2021-12-31" and z["label_end_h3"]]
X=lambda z:[float(z[k]) for k in FEATURE_NAMES]
mu=[sum(X(z)[j] for z in tr)/len(tr) for j in range(len(FEATURE_NAMES))]
sd=[(sum((X(z)[j]-mu[j])**2 for z in tr)/(len(tr)-1))**.5 or 1 for j in range(len(mu))]
S=lambda z:[(X(z)[j]-mu[j])/sd[j] for j in range(len(mu))]
yt=[y(z) for z in tr];w=fit_logistic([S(z) for z in tr],yt,steps=1400,lr=.03);base=sum(yt)/len(yt)
out={}
for label,a,b in (("2022","2022-01-01","2022-12-31"),("2023","2023-01-01","2023-12-31"),("2024_diag","2024-01-01","2024-12-31"),("2025_diag","2025-01-01","2025-12-31"),("2026_diag","2026-01-01","2026-12-31")):
 ds=[z for z in D if a<=z["decision_date"]<=b and z["label_end_h3"]];yv=[y(z) for z in ds];p=predict(w,[S(z) for z in ds]);q=[base]*len(yv)
 gated=[(z,pp) for z,pp in zip(ds,p) if score_open_features(A,z)["conservative"]>=.8]
 yg=[y(z) for z,_ in gated];pg=[pp for _,pp in gated];qg=[base]*len(yg)
 out[label]={"all":{"n":len(ds),"event_rate":sum(yv)/len(yv),"mean_p":sum(p)/len(p),"delta_brier":brier(yv,q)-brier(yv,p),"delta_logloss":logloss(yv,q)-logloss(yv,p)},
 "activity_gated":{"n":len(gated),"event_rate":sum(yg)/len(yg) if yg else None,"mean_p":sum(pg)/len(pg) if pg else None,
 "delta_brier":brier(yg,qg)-brier(yg,pg) if yg else None,"delta_logloss":logloss(yg,qg)-logloss(yg,pg) if yg else None}}
open("artifacts/o3_downside_mae_stability_v05.json","w").write(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
