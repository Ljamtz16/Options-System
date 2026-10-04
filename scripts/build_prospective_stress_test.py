import json
from pathlib import Path
from options_system.prospective_stress_testing import run_stress_test

ROOT = Path(__file__).resolve().parents[1]
out = ROOT / "artifacts" / "intraday" / "PROSPECTIVE_STRESS_TEST_V01.json"
payload = {"version": "v0.1", "do_not_use_as_hypothesis_evidence": True, **run_stress_test(1000.0)}
out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print("STRESS_TEST_OK", "scenarios", len(payload["scenarios"]))
