from src.options_system.path_activity_gate import path_activity_gate
def test_activity_requires_lower_neither():
 assert path_activity_gate(.12,.32)["activity_supported"]
def test_no_activity_edge_when_similar():
 assert not path_activity_gate(.30,.32)["activity_supported"]
