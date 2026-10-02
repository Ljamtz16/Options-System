from datetime import date,timedelta
from .underlying_history import spy_reference_at
from .contract_catalog import fetch_contracts_all_statuses
from .historical_universe import build_universe
from .historical_orchestrator import run_session

def run_day(session_date,start_utc,end_utc,root_dir,max_contracts=None):
    d=date.fromisoformat(session_date)
    ref=spy_reference_at("SPY",start_utc,end_utc)
    spot=ref["price"]
    params={"underlying_symbols":"SPY",
            "expiration_date_gte":str(d+timedelta(days=1)),
            "expiration_date_lte":str(d+timedelta(days=10)),
            "strike_price_gte":str(round(spot*.96,2)),
            "strike_price_lte":str(round(spot*1.04,2)),"limit":1000}
    contracts=fetch_contracts_all_statuses(params)
    universe=build_universe(contracts,d,spot)
    result=run_session(session_date,universe,start_utc,end_utc,root_dir,max_contracts)
    return {"session_date":session_date,"spy_reference":ref,
            "universe_count":len(universe),"run":result}
