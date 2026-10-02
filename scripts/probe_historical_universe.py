from datetime import date
from collections import Counter
from options_system.contract_catalog import fetch_contracts_all_statuses
from options_system.historical_universe import build_universe
session=date(2026,9,29); spot=762.08
contracts=fetch_contracts_all_statuses({"underlying_symbols":"SPY",
 "expiration_date_gte":"2026-09-30","expiration_date_lte":"2026-10-09",
 "strike_price_gte":str(round(spot*.96,2)),"strike_price_lte":str(round(spot*1.04,2)),"limit":1000})
rows=build_universe(contracts,session,spot)
print("catalog=",len(contracts),"eligible=",len(rows))
print("expirations=",dict(sorted(Counter(r["expiration_date"] for r in rows).items())))
print("types=",dict(Counter(r["option_type"] for r in rows)))
