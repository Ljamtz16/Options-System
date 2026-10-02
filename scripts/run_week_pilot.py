import json,time
from pathlib import Path
from options_system.env import load_local_env
load_local_env()
from options_system.session_builder import prepare_session
from options_system.historical_orchestrator import run_session
from options_system.coverage import session_coverage

sessions=[
("2026-09-21","2026-09-21T13:30:00Z","2026-09-21T20:00:00Z"),
("2026-09-22","2026-09-22T13:30:00Z","2026-09-22T20:00:00Z"),
("2026-09-23","2026-09-23T13:30:00Z","2026-09-23T20:00:00Z"),
("2026-09-24","2026-09-24T13:30:00Z","2026-09-24T20:00:00Z"),
("2026-09-25","2026-09-25T13:30:00Z","2026-09-25T20:00:00Z")]
root=Path("data/raw/historical/week_pilot_v01")
summary=[]
for d,s,e in sessions:
    t=time.time()
    m=prepare_session(d,s,e,root/"manifests")
    run=run_session(d,m["universe"],s,e,root/"market",max_contracts=20)
    cov=session_coverage(root/"market"/d)
    summary.append({"date":d,"spot":m["decision_reference"]["price"],
      "eligible":m["contract_count"],"sample":len(cov),
      "with_bars":sum(x["has_bars"] for x in cov),
      "with_trades":sum(x["has_trades"] for x in cov),
      "bars":sum(x["bars"] for x in cov),"trades":sum(x["trades"] for x in cov),
      "failures":len(run["failures"]),"seconds":round(time.time()-t,2)})
    print(summary[-1],flush=True)
(root/"week_summary.json").write_text(json.dumps(summary,indent=2))
