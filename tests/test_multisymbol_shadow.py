import json
from pathlib import Path

from options_system.multisymbol_shadow import active_candidates, derive_row, is_new_episode, summarize_episodes

ROOT = Path(__file__).resolve().parents[1]
CFG = ROOT / "config/multisymbol_shadow_v01.json"
MARKET_FIRST = {"SPY": 100.0, "QQQ": 100.0, "IWM": 100.0}


def test_config_is_shadow_only_and_symbols_are_frozen():
    cfg = json.loads(CFG.read_text(encoding="utf-8"))
    assert cfg["mode"] == "SHADOW_ONLY_NO_ORDERS"
    assert cfg["prospective_start_after"] == "2026-10-14"
    assert cfg["symbols"] == ["SPY", "QQQ", "IWM", "AAPL", "NVDA", "MSFT", "AMZN", "META", "TSLA"]
    assert len(cfg["candidates"]) == 4


def test_put_breakdown_candidate():
    cfg = json.loads(CFG.read_text(encoding="utf-8"))
    history = [{"captured_at_utc": "2026-10-15T14:00:00+00:00", "spot": 100.0}]
    base = {
        "captured_at_utc": "2026-10-15T14:05:00+00:00", "symbol": "NVDA", "spot": 99.4,
        "market_spy_price": 99.8, "market_qqq_price": 99.7, "market_iwm_price": 99.9, "vix_change_pct": 0.08,
    }
    row = derive_row(base, 100.0, history, MARKET_FIRST)
    ids = [c["id"] for c in active_candidates(cfg, row)]
    assert "MS01_PUT_BREAKDOWN_RISKOFF_V01" in ids


def test_call_breakout_candidate():
    cfg = json.loads(CFG.read_text(encoding="utf-8"))
    history = [{"captured_at_utc": "2026-10-15T14:00:00+00:00", "spot": 100.0}]
    base = {
        "captured_at_utc": "2026-10-15T14:05:00+00:00", "symbol": "AAPL", "spot": 100.6,
        "market_spy_price": 100.2, "market_qqq_price": 100.3, "market_iwm_price": 100.1, "vix_change_pct": -0.03,
    }
    row = derive_row(base, 100.0, history, MARKET_FIRST)
    ids = [c["id"] for c in active_candidates(cfg, row)]
    assert "MS02_CALL_BREAKOUT_RISKON_V01" in ids


def test_spy_relative_feature_is_zero():
    row = derive_row({
        "captured_at_utc": "2026-10-15T14:05:00+00:00", "symbol": "SPY", "spot": 101.0,
        "market_spy_price": 101.0,
    }, 100.0, [], MARKET_FIRST)
    assert row["relative_to_spy"] == 0.0


def test_episode_gap_is_strictly_greater_than_six_minutes():
    assert not is_new_episode("2026-10-15T14:00:00+00:00", "2026-10-15T14:06:00+00:00", 6)
    assert is_new_episode("2026-10-15T14:00:00+00:00", "2026-10-15T14:06:02+00:00", 6)


def test_summary_adds_one_contract_pnl():
    candidate={"id":"MSX","side":"PUT"}
    rows=[
        {"candidate_id":"MSX","entry_put_ask":2.0,"put_terminal_return_30m":0.10,"put_best_return_30m":0.2,"put_worst_return_30m":-0.05,"put_30m_tp10_sl10":"TP_FIRST"},
        {"candidate_id":"MSX","entry_put_ask":1.5,"put_terminal_return_30m":-0.20,"put_best_return_30m":0.02,"put_worst_return_30m":-0.25,"put_30m_tp10_sl10":"SL_FIRST"},
    ]
    out=summarize_episodes(rows,candidate,(30,))["horizons"]["30"]
    assert out["pnl_1_contract_n"] == 2
    assert abs(out["total_pnl_1_contract"] + 10.0) < 1e-9
    assert abs(out["mean_pnl_1_contract"] + 5.0) < 1e-9
