import json,runpy
from options_system.env import load_local_env
from options_system.spy_daily import fetch_daily_spy
from options_system.direction_model import fit_logistic,predict,brier,logloss
load_local_env();r=fetch_daily_spy("2018-11-01T00:00:00Z","2026-09-01T00:00:00Z")
def f(i):
 if i<61:return None
 c=[float(x["close"]) for x in r[:i]];op=float(r[i]["open"]);pc=c[-1];d=[c[k]/c[k-1]-1 for k in range(len(c)-20,len(c))];m=sum(d)/20;v=(sum((x-m)**2 for x in d)/19)**.5
 return [c[-1]/c[-2]-1,c[-1]/c[-3]-1,c[-1]/c[-6]-1,c[-1]/c[-11]-1,c[-1]/c[-21]-1,op/pc-1,v,pc/(sum(c[-20:])/20)-1,pc/(sum(c[-50:])/50)-1]
data=[]
for i in range(len(r)-2):
 x=f(i);ret=float(r[i+2]["close"])/float(r[i]["open"])-1
 if x and abs(ret)>=.01:data.append((r[i]["date"],x,1 if ret>0 else 0))
tr=[z for z in data if z[0]<="2021-12-31"];va=[z for z in data if "2022-01-01"<=z[0]<="2023-12-31"];oo=[z for z in data if z[0]>="2024-01-01"]
mu=[sum(z[1][j] for z in tr)/len(tr) for j in range(9)];sd=[(sum((z[1][j]-mu[j])**2 for z in tr)/(len(tr)-1))**.5 or 1 for j in range(9)];S=lambda z:[(z[1][j]-mu[j])/sd[j] for j in range(9)]
w=fit_logistic([S(z) for z in tr],[z[2] for z in tr])
def M(z):
 y=[a[2] for a in z];p=predict(w,[S(a) for a in z]);base=sum(a[2] for a in tr)/len(tr);bp=[base]*len(y)
 return {"n":len(y),"up_rate":sum(y)/len(y),"baseline_p":base,"delta_brier":brier(y,bp)-brier(y,p),"delta_logloss":logloss(y,bp)-logloss(y,p),"mean_model_p":sum(p)/len(p)}
out={"target":"P(UP | abs(H3 OPEN terminal return)>=1%)","train":M(tr),"validation":M(va),"inspected_2024_2026_diagnostic":M(oo)}
open("artifacts/o3_direction_given_magnitude_h3_open_v01.json","w").write(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
