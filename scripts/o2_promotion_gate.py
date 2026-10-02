import json
p="artifacts/o2/o2_target_sweep_v01.json";rows=json.load(open(p))
for r in rows:
 if "baseline" not in r:continue
 db=r["baseline"]["brier"]-r["best"]["metrics"]["brier"]
 dl=r["baseline"]["logloss"]-r["best"]["metrics"]["logloss"]
 r["delta_brier"]=db;r["delta_logloss"]=dl
 r["promotion_candidate"]=bool(r.get("supported") and db>=.005 and dl>=.01)
 r["promotion_reason"]="PASS_MIN_EFFECT" if r["promotion_candidate"] else "INSUFFICIENT_VALIDATION_GAIN"
json.dump(rows,open("artifacts/o2/o2_target_sweep_v02.json","w"),indent=2)
print(json.dumps([{"target":r["target"],"delta_brier":round(r.get("delta_brier",0),6),"delta_logloss":round(r.get("delta_logloss",0),6),"promote":r.get("promotion_candidate")} for r in rows if r.get("supported")],indent=2))
