from options_system.vix_context import fetch_vix
def test_vix_live_contract():
 x=fetch_vix()
 assert x["source"]=="CBOE_DELAYED"
 assert x["current_price"]>0
 assert x["timestamp"] is not None
