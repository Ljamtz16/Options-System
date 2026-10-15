from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_multisymbol_arbitration_runs_after_multisymbol_discovery():
    code = (ROOT / "scripts/vps_postclose.py").read_text(encoding="utf-8")
    discovery = '"scripts/build_multisymbol_discovery.py"'
    arbitration = '"scripts/build_multisymbol_signal_arbitration.py"'
    report = '"scripts/hypothesis_daily_report.py"'
    assert discovery in code
    assert arbitration in code
    assert report in code
    assert code.index(discovery) < code.index(arbitration) < code.index(report)
