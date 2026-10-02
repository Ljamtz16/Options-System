from src.options_system.open_first_touch import first_touch_open
def test_up_first():
 r=[{"open":100,"high":101,"low":99.8},{"open":100,"high":100,"low":99},{"open":100,"high":100,"low":99}]
 assert first_touch_open(r,0,3,.005,.005)["label"]=="UP"
def test_down_first():
 r=[{"open":100,"high":100.2,"low":99.4},{"open":100,"high":101,"low":99},{"open":100,"high":100,"low":99}]
 assert first_touch_open(r,0,3,.005,.005)["label"]=="DOWN"
def test_same_session_ambiguous():
 r=[{"open":100,"high":101,"low":99},{"open":100,"high":100,"low":100},{"open":100,"high":100,"low":100}]
 assert first_touch_open(r,0,3,.005,.005)["label"]=="AMBIGUOUS_SAME_SESSION"
def test_incomplete_none():
 assert first_touch_open([{"open":100,"high":101,"low":99}],0,3) is None
