from src.options_system.outcomes import forward_returns,path_outcomes
def test_forward_return_and_barrier_order():
 x=[("a",100),("b",101),("c",99),("d",102)]
 r=forward_returns(x,(1,)); assert round(r[0]["ret_h1"],4)==.01
 p=path_outcomes(x,3,.005,.005); assert p[0]["up_before_down"] is True
def test_tail_targets_are_missing():
 x=[("a",100),("b",101)]
 assert forward_returns(x,(3,))[0]["ret_h3"] is None
