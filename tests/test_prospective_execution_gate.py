from options_system.prospective_execution_gate import evaluate_execution

G={"status":"ACTIVE","allowed_max_fraction":.20}

def ep(**kw):
    x={"contract":"SPY_CALL","entry_ask":1.50,"entry_bid":1.45,"entry_bid_size":10,"entry_ask_size":20}
    x.update(kw); return x

def test_good_contract_passes():
    x=evaluate_execution(ep(),G,1000)
    assert x["status"]=="PASS"
    assert x["executable"] is True
    assert x["max_contracts_by_risk_budget"]==1

def test_missing_quality_is_review_not_pass():
    x=evaluate_execution({"contract":"SPY_CALL","entry_ask":1.50},G,1000)
    assert x["status"]=="REVIEW_MISSING_MARKET_QUALITY"
    assert set(x["missing_market_quality"])=={"entry_bid","entry_bid_size","entry_ask_size"}

def test_risk_gate_block_always_blocks():
    x=evaluate_execution(ep(),{"status":"BLOCKED","allowed_max_fraction":0},1000)
    assert x["status"]=="BLOCK"
    assert "RISK_GATE_BLOCKED" in x["reasons"]

def test_expensive_contract_blocks_on_budget():
    x=evaluate_execution(ep(entry_ask=2.50,entry_bid=2.45),G,1000)
    assert x["status"]=="BLOCK"
    assert "INSUFFICIENT_RISK_BUDGET" in x["reasons"]

def test_wide_spread_blocks():
    x=evaluate_execution(ep(entry_ask=1.50,entry_bid=1.20),G,1000)
    assert x["status"]=="BLOCK"
    assert "SPREAD_ABOVE_LIMIT" in x["reasons"]

def test_low_liquidity_blocks():
    x=evaluate_execution(ep(entry_bid_size=0,entry_ask_size=0),G,1000)
    assert x["status"]=="BLOCK"
    assert "ENTRY_BID_SIZE_BELOW_LIMIT" in x["reasons"]
    assert "ENTRY_ASK_SIZE_BELOW_LIMIT" in x["reasons"]

def test_contract_price_limit_is_independent_of_budget():
    x=evaluate_execution(ep(entry_ask=5.50,entry_bid=5.45),{"status":"ACTIVE","allowed_max_fraction":.80},1000)
    assert "CONTRACT_PRICE_ABOVE_LIMIT" in x["reasons"]

def test_market_quality_can_be_nonmandatory_for_diagnostics():
    x=evaluate_execution({"contract":"SPY_CALL","entry_ask":1.50},G,1000,{"require_market_quality":False})
    assert x["status"]=="PASS"
