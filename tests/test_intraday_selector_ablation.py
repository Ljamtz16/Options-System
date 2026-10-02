from datetime import date
from options_system.intraday_contract_selector import select_grid
from options_system.intraday_ablation import cumulative_feature_sets,readiness

def test_selector_grid_and_ablation():
 chain={"snapshots":{
  "SPY261002C00770000":{"greeks":{"delta":.50},"latestQuote":{"bp":1.0,"ap":1.05}},
  "SPY261002P00770000":{"greeks":{"delta":-.50},"latestQuote":{"bp":1.1,"ap":1.15}}}}
 g=select_grid(chain,date(2026,10,2))
 assert "call_50d_dte0_0" in g and "put_50d_dte0_0" in g
 sets=cumulative_feature_sets();assert sets[-1]["through"]=="options"
 assert readiness([],200,10)["ready"] is False