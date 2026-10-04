import json
from pathlib import Path
from options_system.prospective_risk_gate import build_risk_gate

ROOT=Path(__file__).resolve().parents[1]
A=ROOT/"artifacts"/"intraday"
report_path=A/"HYPOTHESIS_DAILY_REPORT_V02.json"
stress_path=A/"PROSPECTIVE_STRESS_TEST_V01.json"
report=json.loads(report_path.read_text(encoding="utf-8")) if report_path.exists() else {"prospective_episodes":[],"virtual_account":{"ledger":[]}}
stress=json.loads(stress_path.read_text(encoding="utf-8")) if stress_path.exists() else {"scenarios":{}}
payload=build_risk_gate(report,stress)
out=A/"PROSPECTIVE_RISK_GATE_V01.json"
out.write_text(json.dumps(payload,indent=2),encoding="utf-8")
print("RISK_GATE_OK", "status",payload["status"],"tier",payload["evidence"]["tier"],"allowed",payload["allowed_max_fraction"],"strategy",payload["recommended_strategy"])
