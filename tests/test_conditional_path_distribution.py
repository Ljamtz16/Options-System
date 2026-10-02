from options_system.conditional_path_distribution import split_path_scenarios,mixture_path_weights
def test_path_event_not_terminal_event():
 s=[{"terminal_return":0.0,"mfe":.02,"mae":-.002},{"terminal_return":.02,"mfe":.005,"mae":-.004}]
 e,n=split_path_scenarios(s,.01);assert e[0]==0.0 and n[0]==.02
def test_weights_sum_one_and_keep_group():
 w=mixture_path_weights(.6,[.01,.02],[0]);assert abs(sum(x[1] for x in w)-1)<1e-12 and {x[2] for x in w}=={"EVENT","NON_EVENT"}
