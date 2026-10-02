import json
from datetime import date,timedelta
from pathlib import Path
from .underlying_history import causal_spot_reference
from .contract_catalog import fetch_contracts_all_statuses
from .historical_universe import build_universe

def prepare_session(session_date,start_utc,end_utc,output_root):
    out=Path(output_root)/session_date; out.mkdir(parents=True,exist_ok=True)
    p=out/"universe.json"
    if p.exists():
        return json.loads(p.read_text())
    d=date.fromisoformat(session_date)
    ref=causal_spot_reference("SPY",start_utc,end_utc); spot=ref["price"]
    params={"underlying_symbols":"SPY","expiration_date_gte":str(d+timedelta(days=1)),
      "expiration_date_lte":str(d+timedelta(days=10)),
      "strike_price_gte":str(round(spot*.96,2)),"strike_price_lte":str(round(spot*1.04,2)),"limit":1000}
    contracts=fetch_contracts_all_statuses(params)
    universe=build_universe(contracts,d,spot)
    manifest={"session_date":session_date,"decision_reference":ref,
              "eligibility":{"dte_min":1,"dte_max":10,"width_pct":0.04},
              "contract_count":len(universe),"universe":universe}
    p.write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    return manifest
