from src.options_system.event_labels import first_touch,event_labels
def test_first_touch():
 assert first_touch([.001,.006,-.01],.005,-.005)=="UP"
 assert first_touch([-.006,.02],.005,-.005)=="DOWN"
 assert first_touch([.001,.002],.005,-.005)=="NEITHER"
def test_incomplete_horizon_null():
 x=[("a",100),("b",101)]
 assert event_labels(x,(3,))[0]["up05_dn05_h3"] is None
