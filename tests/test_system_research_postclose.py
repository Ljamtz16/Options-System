from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def test_system_research_runs_after_source_reports_and_before_health_gate():
    code=(ROOT/"scripts/vps_postclose.py").read_text(encoding="utf-8")
    multi='"scripts/build_multisymbol_signal_arbitration.py"'
    h01='"scripts/analyze_h01_execution_diagnostics.py"'
    path='"scripts/analyze_h01_path_policies.py"'
    research='"scripts/analyze_system_research_diagnostics.py"'
    health='"scripts/analyze_strategy_health_gate.py"'
    overlay='"scripts/analyze_h01_risk_overlay_shadow.py"'
    assert all(x in code for x in (multi,h01,path,research,health,overlay))
    assert code.index(multi) < code.index(research)
    assert code.index(h01) < code.index(path) < code.index(research) < code.index(health) < code.index(overlay)
