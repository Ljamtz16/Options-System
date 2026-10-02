from options_system.activity_operating_point import activity_operating_point
def test_activity_gate():
 assert activity_operating_point(.81)["activity_pass"] and not activity_operating_point(.79)["activity_pass"]
