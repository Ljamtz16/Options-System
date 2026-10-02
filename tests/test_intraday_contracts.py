from datetime import date
from options_system.intraday_contracts import representative_contracts,conservative_long_pnl

def test_representative_contracts_and_pnl():
    chain={"snapshots":{
      "SPY261002C00770000":{"greeks":{"delta":.51},"latestQuote":{"bp":1.9,"ap":2.0}},
      "SPY261002P00770000":{"greeks":{"delta":-.49},"latestQuote":{"bp":2.1,"ap":2.2}}}}
    reps=representative_contracts(chain,date(2026,10,2))
    assert reps["call"]["symbol"].endswith("C00770000")
    assert reps["put"]["symbol"].endswith("P00770000")
    later={"snapshots":{"SPY261002C00770000":{"latestQuote":{"bp":2.4,"ap":2.5}}}}
    p=conservative_long_pnl(reps["call"],later)
    assert round(p["pnl_usd"],6)==40.0
    assert round(p["return"],6)==0.2
