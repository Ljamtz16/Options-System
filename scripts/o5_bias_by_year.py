import csv,json
rows=list(csv.DictReader(open("artifacts/o5_walkforward_spy_2024_2026.csv")))
out={}
for y in ("2024","2025","2026"):
 z=[r for r in rows if r["date"].startswith(y)]
 out[y]={"n":len(z),"actual_mean_h3":sum(float(r["actual_h3"]) for r in z)/len(z),"actual_up_rate":sum(float(r["actual_h3"])>0 for r in z)/len(z),
 "positive_ev_rate":sum(float(r["ev"])>0 for r in z)/len(z),"best_call_rate":sum(r["type"]=="call" for r in z)/len(z),
 "positive_call":sum(r["type"]=="call" and float(r["ev"])>0 for r in z),"positive_put":sum(r["type"]=="put" and float(r["ev"])>0 for r in z)}
open("artifacts/o5_call_put_bias_by_year_v01.json","w").write(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
