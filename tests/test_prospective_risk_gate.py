from options_system.prospective_risk_gate import evidence_cap, stress_cap, build_risk_gate

def stress(dd20=.10,dd40=.15,dd60=.22,dd80=.30):
    return {"scenarios":{"adverse":{"strategies":{
        "pct_20":{"max_drawdown_pct":dd20},"pct_40":{"max_drawdown_pct":dd40},
        "pct_60":{"max_drawdown_pct":dd60},"pct_80":{"max_drawdown_pct":dd80},
    }}}}

def report(n):
    eps=[{"tp_sl":"TP_FIRST"} for _ in range(n)]
    ledger=[{"execution_status":"EXECUTED"} for _ in range(n)]
    return {"prospective_episodes":eps,"virtual_account":{"ledger":ledger}}

def test_zero_evidence_is_capped_at_20_percent():
    assert evidence_cap(0,0)=={"max_fraction":.20,"tier":"BOOTSTRAP"}

def test_evidence_unlocks_only_predefined_tiers():
    assert evidence_cap(19,19)["max_fraction"]==.20
    assert evidence_cap(20,20)["max_fraction"]==.40
    assert evidence_cap(50,50)["max_fraction"]==.60
    assert evidence_cap(100,100)["max_fraction"]==.80

def test_stress_cap_uses_worst_scenario_and_limit():
    s={"scenarios":{
        "a":{"strategies":{"pct_20":{"max_drawdown_pct":.10},"pct_40":{"max_drawdown_pct":.15},"pct_60":{"max_drawdown_pct":.18},"pct_80":{"max_drawdown_pct":.19}}},
        "b":{"strategies":{"pct_20":{"max_drawdown_pct":.11},"pct_40":{"max_drawdown_pct":.16},"pct_60":{"max_drawdown_pct":.21},"pct_80":{"max_drawdown_pct":.31}}},
    }}
    x=stress_cap(s,.20)
    assert x["max_fraction"]==.40

def test_gate_takes_lower_of_evidence_and_stress_caps():
    g=build_risk_gate(report(100),stress(),.20)
    assert g["evidence"]["max_fraction"]==.80
    assert g["stress"]["max_fraction"]==.40
    assert g["allowed_max_fraction"]==.40
    assert g["recommended_strategy"]=="pct_40"

def test_no_prospective_evidence_never_unlocks_above_20():
    g=build_risk_gate(report(0),stress(.05,.05,.05,.05),.20)
    assert g["allowed_max_fraction"]==.20
    assert g["evidence"]["tier"]=="BOOTSTRAP"

def test_no_stress_data_defaults_to_20_percent_cap():
    g=build_risk_gate(report(100),{"scenarios":{}},.20)
    assert g["allowed_max_fraction"]==.20
    assert g["stress"]["reason"]=="NO_STRESS_DATA"

def test_if_even_20_percent_breaks_limit_gate_blocks_trading():
    g=build_risk_gate(report(100),stress(.25,.30,.40,.50),.20)
    assert g["status"]=="BLOCKED"
    assert g["allowed_max_fraction"]==0
    assert g["recommended_strategy"]=="NO_TRADE"

def test_gate_is_governance_not_hypothesis_evidence():
    g=build_risk_gate(report(0),stress(),.20)
    assert g["scientific_evidence"] is False
    assert g["rules"]["diagnostic_history_does_not_unlock_sizing"] is True
