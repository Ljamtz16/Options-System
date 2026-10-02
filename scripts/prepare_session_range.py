import argparse
from datetime import date,timedelta
from options_system.market_calendar import regular_session_utc
from options_system.session_builder import prepare_session

p=argparse.ArgumentParser()
p.add_argument("--start",required=True); p.add_argument("--end",required=True)
p.add_argument("--out",default="data/raw/historical/session_manifests")
a=p.parse_args(); d=date.fromisoformat(a.start); end=date.fromisoformat(a.end)
while d<=end:
    if d.weekday()<5:
        s,e=regular_session_utc(d)
        try:
            m=prepare_session(d.isoformat(),s,e,a.out)
            print(d,"spot=",m["decision_reference"]["price"],"contracts=",m["contract_count"])
        except RuntimeError as exc:
            if "No contemporaneous stock bars" in str(exc): print(d,"NO_SESSION")
            else: raise
    d+=timedelta(days=1)
