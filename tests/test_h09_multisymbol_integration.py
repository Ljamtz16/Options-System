from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_postclose_rebuilds_shadow_reports_before_dashboard_meta():
    code = (ROOT / "scripts/vps_postclose.py").read_text(encoding="utf-8")
    h09 = '"scripts/run_h09_put_flow_shadow.py"'
    multi = '"scripts/build_multisymbol_discovery.py"'
    meta = '"scripts/build_research_dashboard_meta.py"'
    assert h09 in code and multi in code and meta in code
    assert code.index(h09) < code.index(meta)
    assert code.index(multi) < code.index(meta)


def test_live_shadow_runners_cannot_submit_broker_orders():
    for name in ("run_h09_put_flow_live.py", "run_multisymbol_shadow_live.py"):
        code = (ROOT / "scripts" / name).read_text(encoding="utf-8")
        assert '"broker_orders_enabled": False' in code
        assert "AlpacaPaperClient" not in code
        assert "run_options_alpaca_mirror" not in code


def test_user_services_are_persistent_default_target():
    for name in ("options-h09-put-flow-live.service", "options-multisymbol-shadow.service"):
        unit = (ROOT / "deploy/systemd" / name).read_text(encoding="utf-8")
        assert "WantedBy=default.target" in unit
        assert "Restart=always" in unit


def test_dashboard_meta_exposes_both_shadow_labs():
    code = (ROOT / "scripts/build_research_dashboard_meta.py").read_text(encoding="utf-8")
    assert "'h09_live':h09_live" in code
    assert "'multisymbol_live':multisymbol_live" in code
    html = (ROOT / "artifacts/intraday/intraday_research_dashboard.html").read_text(encoding="utf-8")
    assert "shadow_labs_widget.js" in html
