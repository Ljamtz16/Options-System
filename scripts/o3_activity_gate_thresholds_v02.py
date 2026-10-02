import csv,json
from options_system.open_probability_runtime import load_probability_artifact,score_open_features
A=load_probability_artifact("artifacts/o3/O3_OPEN_PATH_H3_PROB_V02.json")
D=list(csv.DictReader(open("data/processed/o2_open/spy_open_outcomes_v02.csv")))
def event(z):return max(float(z["mfe_h3"]),-float(z["mae_h3"]))>=.01
def score_rows(rows):
 out=[]
 for z in rows:
  if not z["label_end_h3"]:continue
  p=score_open_features(A,z);out.append((z["decision_date"],p["conservative"],event(z)))
 return out
va=score_rows([z for z in D if "2022-01-01"<=z["decision_date"]<="2023-12-31"])
dg=score_rows([z for z in D if z["decision_date"]>="2024-01-01"])
def sweep(rows):
 out={}
 for t in (.5,.6,.7,.8,.9):
  sel=[x for x in rows if x[1]>=t]
  out[str(t)]={"n":len(sel),"coverage":len(sel)/len(rows),"event_rate":sum(x[2] for x in sel)/len(sel) if sel else None,
  "false_activity_rate":sum(not x[2] for x in sel)/len(sel) if sel else None}
 return out
out={"validation":sweep(va),"inspected_2024_2026":sweep(dg)}
open("artifacts/o3/o3_activity_gate_thresholds_v02.json","w").write(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
