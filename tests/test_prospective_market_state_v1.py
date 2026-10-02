from datetime import date
from options_system.chain_features import extract_chain_features
from options_system.research_decision_engine import research_decision

def test_chain_features_realistic():
 chain={"snapshots":{
  "SPY261006C00770000":{"impliedVolatility":.20,"latestQuote":{"bp":2.0,"ap":2.2},"dailyBar":{"v":100},"greeks":{"delta":.5,"gamma":.02,"vega":.1}},
  "SPY261006P00770000":{"impliedVolatility":.24,"latestQuote":{"bp":2.1,"ap":2.3},"dailyBar":{"v":150},"greeks":{"delta":-.5,"gamma":.02,"vega":.11}}
 }}
 x=extract_chain_features(chain,770,date(2026,10,2))
 assert x["contract_count"]==2
 assert abs(x["put_call_iv_skew"]-.04)<1e-12
 assert x["put_call_volume_ratio_1pct"]==1.5

def test_o6_still_blocks_no_direction():
 assert research_decision(True,False,"NONE",0,True,10,True,True)["decision"]=="NO_TRADE_DIRECTION"
