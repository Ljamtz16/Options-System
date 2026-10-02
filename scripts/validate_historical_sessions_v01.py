from options_system.env import load_local_env
load_local_env()
from options_system.session_builder import prepare_session
sessions=[
("2026-09-25","2026-09-25T13:30:00Z","2026-09-25T20:00:00Z"),
("2026-09-28","2026-09-28T13:30:00Z","2026-09-28T20:00:00Z"),
("2026-09-29","2026-09-29T13:30:00Z","2026-09-29T20:00:00Z")]
for d,s,e in sessions:
    try:
        m=prepare_session(d,s,e,"data/raw/historical/session_manifests_v01")
        r=m["decision_reference"]
        print(d,"spot=",r["price"],"at=",r["observed_at_utc"],"contracts=",m["contract_count"])
    except Exception as exc:
        print(d,"ERROR",type(exc).__name__,str(exc))

