import json
from pathlib import Path
from options_system.prospective_sizing_simulator import compare_sizing

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / "artifacts" / "intraday"
report_path = A / "HYPOTHESIS_DAILY_REPORT_V02.json"
out = A / "PROSPECTIVE_SIZING_COMPARISON_V01.json"

if report_path.exists():
    report = json.loads(report_path.read_text(encoding="utf-8"))
    episodes = report.get("prospective_episodes", [])
else:
    episodes = []

payload = {
    "version": "v0.1",
    "do_not_use_as_hypothesis_evidence": True,
    **compare_sizing(episodes, initial_cash=1000.0),
}
out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print("SIZING_COMPARISON_OK", "episodes", len(episodes), "strategies", len(payload["strategies"]))
