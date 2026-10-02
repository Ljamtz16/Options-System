from src.options_system.direction_guard import directional_edge_guard
def test_no_direction_from_baseline_drift():assert directional_edge_guard(.57,.57)["direction"]=="NONE"
def test_up_requires_incremental_edge():assert directional_edge_guard(.64,.57)["direction"]=="UP"
def test_down_requires_incremental_edge():assert directional_edge_guard(.49,.57)["direction"]=="DOWN"
