import csv,json,collections
D=list(csv.DictReader(open("artifacts/o5_o3_walkforward_2024_2026_v03.csv")))
out={}
for year in ("2024","2025","2026"):
 rows=[x for x in D if x["date"].startswith(year)];passes=[x for x in rows if x["activity_pass"]=="True"];surv=[x for x in passes if x["best_symbol"]]
 out[year]={"sessions":len(rows),"activity_pass":len(passes),"activity_pass_rate":len(passes)/len(rows) if rows else None,
 "activity_event_rate":sum(x["actual_event"]=="True" for x in passes)/len(passes) if passes else None,
 "robust_sessions":len(surv),"robust_rate_all":len(surv)/len(rows) if rows else None,
 "best_type_counts":{"call":sum(x["best_type"]=="call" for x in surv),"put":sum(x["best_type"]=="put" for x in surv)},
 "mean_best_ev":sum(float(x["best_ev"]) for x in surv)/len(surv) if surv else None}
open("artifacts/o5_o3_walkforward_2024_2026_v03_by_year.json","w").write(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
