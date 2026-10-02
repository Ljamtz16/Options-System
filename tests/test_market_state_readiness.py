from options_system.market_state_readiness import market_state_training_readiness
def test_readiness_blocks_tiny_dataset():
 rows=[{"decision_date":"2026-10-02","h3_up":"True"}]
 x=market_state_training_readiness(rows);assert not x["ready"];assert "INSUFFICIENT_LABELED_DAYS" in x["reasons"]
