from src.options_system.synthetic_chain import synthetic_chain
def test_chain_size_and_labels():
 r=synthetic_chain(100,dtes=(3,5),moneyness=(-.01,0,.01));assert len(r)==12 and all(x["source"]=="SIMULATED" for x in r)
def test_quotes_valid():
 assert all(x["ask"]>x["bid"]>0 for x in synthetic_chain(100,dtes=(5,),moneyness=(0,)))
