from collections import Counter
from options_system.session_builder import prepare_session
for d in ("2026-09-28","2026-09-29","2026-09-30"):
    m=prepare_session(d,d+"T13:30:00Z",d+"T20:00:00Z","data/raw/historical/session_manifests")
    c=Counter(x["expiration_date"] for x in m["universe"])
    print(d,"spot=",m["decision_reference"]["price"],"contracts=",m["contract_count"],
          "expirations=",len(c))
