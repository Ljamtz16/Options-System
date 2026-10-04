import json
from pathlib import Path
from options_system.prospective_execution_gate import evaluate_episodes

ROOT=Path(__file__).resolve().parents[1]
A=ROOT/"artifacts"/"intraday"
report_path=A/"HYPOTHESIS_DAILY_REPORT_V02.json"
gate_path=A/"PROSPECTIVE_RISK_GATE_V01.json"
report=json.loads(report_path.read_text(encoding="utf-8")) if report_path.exists() else {"prospective_episodes":[]}
gate=json.loads(gate_path.read_text(encoding="utf-8")) if gate_path.exists() else {"status":"BLOCKED","allowed_max_fraction":0}
episodes=report.get("prospective_episodes",[])
cash=float(report.get("virtual_account",{}).get("final_cash",1000.0))
evaluated=evaluate_episodes(episodes,gate,cash)
counts={k:sum(x["execution_gate"]["status"]==k for x in evaluated) for k in ("PASS","BLOCK","REVIEW_MISSING_MARKET_QUALITY")}
payload={
 "version":"v0.1","scientific_evidence":False,
 "purpose":"contract_execution_quality_governance_only",
 "cash_reference":cash,"risk_gate_status":gate.get("status"),
 "allowed_max_fraction":gate.get("allowed_max_fraction",0),
 "counts":counts,"episodes":evaluated,
}
(A/"PROSPECTIVE_EXECUTION_GATE_V01.json").write_text(json.dumps(payload,indent=2),encoding="utf-8")
print("EXECUTION_GATE_OK","episodes",len(evaluated),"pass",counts["PASS"],"block",counts["BLOCK"],"review",counts["REVIEW_MISSING_MARKET_QUALITY"])
