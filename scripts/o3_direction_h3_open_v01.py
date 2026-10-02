import json,math
from options_system.env import load_local_env
from options_system.spy_daily import fetch_daily_spy
from options_system.direction_model import fit_logistic,predict,brier,logloss
load_local_env();r=fetch_daily_spy("2018-11-01T00:00:00Z","2026-09-01T00:00:00Z")
def feat(i):
 prev=[float(x["close"]) for x in r[:i]]
 if i<61:return None
 op=float(r[i]["open"]);pc=prev[-1]
 rets=[prev[-1]/prev[-2]-1,prev[-1]/prev[-3]-1,prev[-1]/prev[-6]-1,prev[-1]/prev[-11]-1,prev[-1]/prev[-21]-1]
 daily=[prev[k]/prev[k-1]-1 for k in range(len(prev)-20,len(prev))]
 vol=(sum((x-sum(daily)/len(daily))**2 for x in daily)/(len(daily)-1))**.5
 sma20=sum(prev[-20:])/20;sma50=sum(prev[-50:])/50
 return rets+[op/pc-1,vol,pc/sma20-1,pc/sma50-1]
data=[]
for i in range(len(r)-2):
 x=feat(i)
 if x:data.append((r[i]["date"],x,1 if float(r[i+2]["close"])/float(r[i]["open"])-1>0 else 0))
tr=[z for z in data if z[0]<="2021-12-31"];va=[z for z in data if "2022-01-01"<=z[0]<="2023-12-31"];oo=[z for z in data if z[0]>="2024-01-01"]
mu=[sum(z[1][j] for z in tr)/len(tr) for j in range(len(tr[0][1]))];sd=[(sum((z[1][j]-mu[j])**2 for z in tr)/(len(tr)-1))**.5 or 1 for j in range(len(mu))]
S=lambda z:[(z[1][j]-mu[j])/sd[j] for j in range(len(mu))]
w=fit_logistic([S(z) for z in tr],[z[2] for z in tr])
def metrics(z):
 y=[a[2] for a in z];p=predict(w,[S(a) for a in z]);base=sum(x[2] for x in tr)/len(tr);bp=[base]*len(y)
 return {"n":len(y),"event_rate":sum(y)/len(y),"baseline_p":base,"model_brier":brier(y,p),"baseline_brier":brier(y,bp),"delta_brier":brier(y,bp)-brier(y,p),"model_logloss":logloss(y,p),"baseline_logloss":logloss(y,bp),"delta_logloss":logloss(y,bp)-logloss(y,p),"mean_model_p":sum(p)/len(p),"edge_ge_5pp_rate":sum(abs(q-base)>=.05 for q in p)/len(p)}
out={"features":["ret1_prev","ret2_prev","ret5_prev","ret10_prev","ret20_prev","gap_open","vol20_prev","close_sma20_prev","close_sma50_prev"],"train":metrics(tr),"validation":metrics(va),"inspected_2024_2026_diagnostic":metrics(oo),"weights":w}
open("artifacts/o3_direction_h3_open_v01.json","w").write(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
