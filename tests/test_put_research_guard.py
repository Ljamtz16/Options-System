from options_system.put_research_guard import put_research_eligibility
def test_put_requires_validated_down_edge():
 assert put_research_eligibility(True,True,"DOWN",.56,.50,10,True)["eligible"]
def test_no_put_without_direction():
 assert not put_research_eligibility(True,False,"NONE",.60,.50,10,True)["eligible"]
def test_no_put_below_edge():
 assert not put_research_eligibility(True,True,"DOWN",.54,.50,10,True)["eligible"]
def test_no_put_negative_ev():
 assert not put_research_eligibility(True,True,"DOWN",.60,.50,-1,True)["eligible"]
