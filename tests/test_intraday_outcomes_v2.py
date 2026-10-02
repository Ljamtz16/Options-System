from options_system.intraday_outcomes import path_outcomes,contract_path_outcomes
from options_system.intraday_targets import option_trade_targets

def test_path_outcomes_and_first_touch():
 x=path_outcomes([100.3,99.6,100.1],100)
 assert x["mfe"]>=.003-1e-12
 assert x["mae"]<=-.004+1e-12
 assert x["first_touch_25bp"]=="UP"

def test_contract_path_and_tp_sl():
 entry={"symbol":"X","ask":1.0}
 snaps=[{"snapshots":{"X":{"latestQuote":{"bp":1.12}}}},
        {"snapshots":{"X":{"latestQuote":{"bp":.85}}}}]
 x=contract_path_outcomes(entry,snaps)
 assert x["best_return"]>=.12-1e-12
 t=option_trade_targets([.12,-.15],"call_30m")
 assert t["call_30m_tp10_sl10"]=="TP_FIRST"