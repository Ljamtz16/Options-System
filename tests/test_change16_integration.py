from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def test_dashboard_is_not_trading_driver():
    code=(ROOT/'scripts/publish_intraday_dashboard_live.py').read_text()
    assert 'scripts/run_live_paper_trader.py' not in code
    assert 'scripts/run_options_alpaca_mirror.py' not in code
    assert 'collector_coverage_widget.js' in code


def test_postclose_keeps_put_frozen_and_adds_diagnostic_only():
    code=(ROOT/'scripts/vps_postclose.py').read_text()
    frozen='"scripts/track_put_confirmation_shadow_v02.py"'
    diagnostic='"scripts/analyze_put_execution_diagnostics.py"'
    report='"scripts/hypothesis_daily_report.py"'
    assert code.index(frozen) < code.index(diagnostic) < code.index(report)


def test_dashboard_meta_exposes_coverage_and_put_diagnostics():
    code=(ROOT/'scripts/build_research_dashboard_meta.py').read_text()
    assert "'collector_coverage':collector_coverage" in code
    assert "'put_execution_diagnostics':put_execution_diagnostics" in code


def test_dashboard_loads_coverage_widget():
    html=(ROOT/'artifacts/intraday/intraday_research_dashboard.html').read_text()
    assert "loadDashboardScript('collector_coverage_widget.js')" in html
