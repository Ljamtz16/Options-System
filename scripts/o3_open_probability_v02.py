import csv,json
from options_system.direction_model import fit_logistic,predict,brier,logloss
from options_system.calibration import fit_platt,apply_platt
from options_system.calibration_metrics import ece
from options_system.probability_guardrail import conservative_probability
from options_system.spy_open_features import FEATURE_NAMES
D=list(csv.DictReader(open("data/processed/o2_open/spy_open_outcomes_v02.csv")))
def y(z):return 1 if max(float(z["mfe_h3"]),-float(z["mae_h3"]))>=.01 else 0
tr=[z for z in D if z["decision_date"]<="2021-12-31" and z["label_end_h3"]];va=[z for z in D if "2022-01-01"<=z["decision_date"]<="2023-12-31" and z["label_end_h3"]];dg=[z for z in D if z["decision_date"]>="2024-01-01" and z["label_end_h3"]]
X=lambda z:[float(z[k]) for k in FEATURE_NAMES];mu=[sum(X(z)[j] for z in tr)/len(tr) for j in range(len(FEATURE_NAMES))];sd=[(sum((X(z)[j]-mu[j])**2 for z in tr)/(len(tr)-1))**.5 or 1 for j in range(len(mu))];S=lambda z:[(X(z)[j]-mu[j])/sd[j] for j in range(len(mu))]
w=fit_logistic([S(z) for z in tr],[y(z) for z in tr],steps=1200,lr=.03);ptr=predict(w,[S(z) for z in tr]);pva=predict(w,[S(z) for z in va]);pdg=predict(w,[S(z) for z in dg]);pl=fit_platt(pva,[y(z) for z in va]);cva=apply_platt(pl,pva);cdg=apply_platt(pl,pdg)
def bins(ps,ys):
 out=[]
 for j in range(10):
  ix=[i for i,p in enumerate(ps) if j/10<=p<((j+1)/10 if j<9 else 1.0000001)]
  if ix:
   rate=sum(ys[i] for i in ix)/len(ix);mp=sum(ps[i] for i in ix)/len(ix);out.append({"lo":j/10,"hi":(j+1)/10,"n":len(ix),"mean_p":mp,"event_rate":rate,"wilson_conservative":conservative_probability(mp,rate,len(ix),30)})
 return out
yv=[y(z) for z in va];yd=[y(z) for z in dg];base=sum(y(z) for z in tr)/len(tr)
out={"target":"P(max(MFE_H3,-MAE_H3)>=1%)","train_n":len(tr),"validation_n":len(va),"diagnostic_n":len(dg),"train_base_rate":base,
"validation":{"raw_brier":brier(yv,pva),"cal_brier":brier(yv,cva),"raw_logloss":logloss(yv,pva),"cal_logloss":logloss(yv,cva),"raw_ece":ece(yv,pva)["ece"],"cal_ece":ece(yv,cva)["ece"],"bins":bins(cva,yv)},
"inspected_2024_2026":{"raw_brier":brier(yd,pdg),"cal_brier":brier(yd,cdg),"raw_logloss":logloss(yd,pdg),"cal_logloss":logloss(yd,cdg),"raw_ece":ece(yd,pdg)["ece"],"cal_ece":ece(yd,cdg)["ece"]},
"platt":pl,"model_weights":w}
open("artifacts/o3/o3_open_path_h3_calibration_v02.json","w").write(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
