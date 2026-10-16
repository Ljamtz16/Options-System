from options_system.meta_decision_layer import (
    annotate_episode_metrics,
    decision_from_reasons,
    market_regime,
    multi_correlation_exposure,
)


def test_decision_precedence():
    assert decision_from_reasons(["bad"], ["wait"]) == "BLOCK"
    assert decision_from_reasons([], ["wait"]) == "WAIT"
    assert decision_from_reasons([], []) == "ACCEPT"


def test_market_regime_all3():
    assert market_regime(0.01, 0.02, 0.03) == "RISK_ON"
    assert market_regime(-0.01, -0.02, -0.03) == "RISK_OFF"
    assert market_regime(0.01, -0.02, 0.03) == "MIXED"


def test_episode_and_flicker_annotations():
    rows = [
        {"source": "MULTI", "symbol": "SPY", "side": "CALL", "time": "2026-10-15T14:00:00+00:00"},
        {"source": "MULTI", "symbol": "SPY", "side": "CALL", "time": "2026-10-15T14:05:00+00:00"},
        {"source": "MULTI", "symbol": "SPY", "side": "PUT", "time": "2026-10-15T14:10:00+00:00"},
    ]
    annotate_episode_metrics(rows, 15, 30)
    assert rows[0]["persistence_observations"] == 1
    assert rows[1]["persistence_observations"] == 2
    assert rows[1]["is_episode_repeat"] is True
    assert rows[2]["episode_id"] != rows[1]["episode_id"]
    assert rows[2]["signal_flip_count_30m"] == 1


def test_multi_correlation_exposure():
    rows = [
        {"source": "MULTI", "symbol": "QQQ", "side": "CALL", "time": "2026-10-15T14:00:00+00:00"},
        {"source": "MULTI", "symbol": "NVDA", "side": "CALL", "time": "2026-10-15T14:01:00+00:00"},
        {"source": "MULTI", "symbol": "AAPL", "side": "PUT", "time": "2026-10-15T14:01:00+00:00"},
    ]
    multi_correlation_exposure(rows)
    assert rows[0]["correlated_opportunity_count_2m"] == 2
    assert rows[1]["correlated_opportunity_count_2m"] == 2
    assert rows[2]["correlated_opportunity_count_2m"] == 1


def test_meta_config_is_shadow_only():
    import json
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    cfg = json.loads((root / "config/meta_decision_layer_v01.json").read_text())
    assert cfg["mode"] == "SHADOW_ONLY"
    assert cfg["auto_apply"] is False
    assert cfg["broker_orders_enabled"] is False
    assert cfg["h01"]["health_block_flags"] == [
        "loss_streak_4",
        "rolling5_winrate_below_20pct",
        "vix_up_5pct",
    ]


def test_meta_layer_is_wired_after_health_inputs():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    text = (root / "scripts/vps_postclose.py").read_text()
    health = text.index('"scripts/analyze_strategy_health_gate.py"')
    overlay = text.index('"scripts/analyze_h01_risk_overlay_shadow.py"')
    meta = text.index('"scripts/analyze_meta_decision_layer_v01.py"')
    assert health < overlay < meta
