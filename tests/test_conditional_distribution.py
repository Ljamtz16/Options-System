from src.options_system.conditional_distribution import conditional_samples,mixture_weights
def test_split_and_weights():
 e,n=conditional_samples([-.02,-.005,.004,.03]);assert len(e)==2 and len(n)==2
 w=mixture_weights(.7,e,n);assert abs(sum(x[1] for x in w)-1)<1e-12 and abs(sum(x[1] for x in w if x[2]=="event")-.7)<1e-12
