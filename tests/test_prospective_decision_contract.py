from datetime import date
from options_system.prospective_collector import market_date_from_clock
from options_system.research_decision_engine import research_decision
def test_market_date_uses_clock_timestamp():
 assert market_date_from_clock({"timestamp":"2026-10-02T09:30:00-04:00"})==date(2026,10,2)
def test_direction_lock_blocks_candidate_after_activity():
 x=research_decision(True,False,"NONE",0.0);assert x["decision"]=="NO_TRADE_DIRECTION"
