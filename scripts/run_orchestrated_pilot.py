from datetime import date
from options_system.contract_catalog import fetch_contracts_all_statuses
from options_system.historical_universe import build_universe
from options_system.historical_orchestrator import run_session

session=date(2026,9,29); spot=762.08
params={"underlying_symbols":"SPY","expiration_date_gte":"2026-09-30",
"expiration_date_lte":"2026-10-09","strike_price_gte":str(round(spot*.96,2)),
"strike_price_lte":str(round(spot*1.04,2)),"limit":1000}
u=build_universe(fetch_contracts_all_statuses(params),session,spot)
result=run_session(session.isoformat(),u,"2026-09-29T13:30:00Z","2026-09-29T20:00:00Z",
 "data/raw/historical/orchestrated_pilot",max_contracts=4)
print("universe=",len(u))
print(result)
