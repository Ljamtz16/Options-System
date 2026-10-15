from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_h01_execution_diagnostics_runs_after_daily_report():
    code = (ROOT / "scripts/vps_postclose.py").read_text(encoding="utf-8")
    report = '"scripts/hypothesis_daily_report.py"'
    diag = '"scripts/analyze_h01_execution_diagnostics.py"'
    sizing = '"scripts/build_prospective_sizing_comparison.py"'
    assert report in code
    assert diag in code
    assert sizing in code
    assert code.index(report) < code.index(diag) < code.index(sizing)
