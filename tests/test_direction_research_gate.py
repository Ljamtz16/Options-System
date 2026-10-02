from src.options_system.direction_research_gate import direction_research_status
def test_negative_validation_locks_direction():
 x=direction_research_status(-.001,-.002);assert not x["direction_enabled"] and x["status"]=="NOT_SUPPORTED"
def test_both_metrics_required():
 assert not direction_research_status(.01,-.001)["supported"]
def test_positive_metrics_can_pass():
 assert direction_research_status(.01,.02)["supported"]
