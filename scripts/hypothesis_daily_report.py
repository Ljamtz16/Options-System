import csv,json
from pathlib import Path
from options_system.prospective_episode_tracker import build_episodes,build_virtual_account

ROOT=Path(__file__).resolve().parents[1]
track=ROOT/"data/processed/intraday/prospective_hypothesis_tracker_v02.csv"
freeze_p=ROOT/"artifacts/intraday/FROZEN_HYPOTHESES_V02.json"
out=ROOT/"artifacts/intraday/HYPOTHESIS_DAILY_REPORT_V02.json"
rows=list(csv.DictReader(open(track,encoding="utf-8"))) if track.exists() else []
meta=json.loads(freeze_p.read_text(encoding="utf-8"))
hypotheses=meta["hypotheses"]
by_id={h["id"]:h for h in hypotheses}

days=sorted({r.get("decision_date") for r in rows if r.get("decision_date")})
report={}
for day in days:
    dr=[r for r in rows if r.get("decision_date")==day]
    activations=[]
    for r in dr:
        for hid in [x for x in (r.get("active_hypotheses") or "").split(";") if x]:
            h=by_id[hid];side=h["side"];hz=int(h["horizon_min"])
            activations.append({
                "hypothesis":hid,"captured_at_utc":r.get("captured_at_utc"),
                "side":side,"horizon_min":hz,"spot":r.get("spot"),
                "contract":r.get(f"{side}_contract"),"entry_ask":r.get(f"{side}_entry_ask"),
                "return":r.get(f"{side}_ret_{hz}m"),"mfe":r.get(f"{side}_mfe_{hz}m"),
                "mae":r.get(f"{side}_mae_{hz}m"),"tp10_sl10":r.get(f"{side}_{hz}m_tp10_sl10")
            })
    report[day]={"snapshots":len(dr),"activations":activations}

episodes=[]
for h in hypotheses:
    episodes.extend(build_episodes(rows,h))
account=build_virtual_account(episodes,1000.0)
payload={"version":"v0.2","frozen_at":meta["frozen_at"],"days":report,
         "prospective_episodes":episodes,"virtual_account":account}
out.write_text(json.dumps(payload,indent=2),encoding="utf-8")
print(f"HYPOTHESIS_REPORT_V02 days={len(days)} activations={sum(len(x['activations']) for x in report.values())} prospective_episodes={len(episodes)} final_cash={account['final_cash']:.2f}")
