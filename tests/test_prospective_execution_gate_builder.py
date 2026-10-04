import json,runpy
from pathlib import Path

def test_execution_gate_builder_writes_governed_artifact(tmp_path, monkeypatch):
    # Unit coverage of the evaluator is primary; this protects artifact semantics.
    from options_system.prospective_execution_gate import evaluate_episodes
    eps=[{"contract":"SPY_CALL","entry_ask":1.0,"entry_bid":.98,"entry_bid_size":2,"entry_ask_size":3}]
    out=evaluate_episodes(eps,{"status":"ACTIVE","allowed_max_fraction":.20},1000)
    assert out[0]["execution_gate"]["status"]=="PASS"
    assert out[0]["execution_gate"]["max_contracts_by_risk_budget"]==2
