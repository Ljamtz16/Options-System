import csv,json,math
from pathlib import Path
from options_system.spy_features import FEATURES
rows=list(csv.DictReader(open("data/processed/o2/spy_outcomes_v01.csv",encoding="utf-8")))
def vals(k): return [r[k] for r in rows if r.get(k) not in ("",None)]
def rate(k,pred):
 x=vals(k);return {"n":len(x),"rate":sum(pred(v) for v in x)/len(x) if x else None}
summary={}
for h in (1,3,5,10):
 summary[f"abs_gt_1pct_h{h}"]=rate(f"abs_gt_1pct_h{h}",lambda v:v=="True")
 for k in ("up05_dn05","up10_dn05","up05_dn10"):
  x=vals(f"{k}_h{h}"); counts={a:x.count(a) for a in ("UP","DOWN","NEITHER","SAME_SESSION")}
  summary[f"{k}_h{h}"]={"n":len(x),"counts":counts}
# descriptive median split association for H10 symmetric event
assoc={}
target="up05_dn05_h10"
for feat in FEATURES:
 pairs=[(float(r[feat]),r[target]) for r in rows if r.get(feat) not in ("",None) and r.get(target) not in ("",None)]
 if not pairs:continue
 s=sorted(x for x,_ in pairs);med=s[len(s)//2]
 def up_rate(group):
  y=[t for x,t in pairs if (x>=med)==group and t in ("UP","DOWN")]
  return (sum(t=="UP" for t in y)/len(y),len(y)) if y else (None,0)
 lo=up_rate(False);hi=up_rate(True)
 assoc[feat]={"median":med,"low_up_rate":lo[0],"low_n":lo[1],"high_up_rate":hi[0],"high_n":hi[1],
 "difference":None if lo[0] is None or hi[0] is None else hi[0]-lo[0]}
out={"scope":"DESCRIPTIVE_ONLY_NOT_PREDICTIVE","sessions":len(rows),"base_rates":summary,"median_split_h10":assoc}
Path("artifacts/o2").mkdir(parents=True,exist_ok=True);Path("artifacts/o2/o2_descriptive_v01.json").write_text(json.dumps(out,indent=2))
print(json.dumps({"sessions":len(rows),"h10_symmetric":summary["up05_dn05_h10"],
"abs1_h10":summary["abs_gt_1pct_h10"],"largest_abs_differences":sorted([(k,v["difference"],v["low_n"],v["high_n"]) for k,v in assoc.items() if v["difference"] is not None],key=lambda x:abs(x[1]),reverse=True)[:5]},indent=2))
