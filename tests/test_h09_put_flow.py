import json
from pathlib import Path

from options_system.h09_put_flow import active_candidates, is_new_episode, live_delta_row, summarize

ROOT = Path(__file__).resolve().parents[1]
CFG = ROOT / "config/h09_put_flow_shadow_v01.json"


def test_config_is_shadow_and_cutoff_is_frozen():
    cfg = json.loads(CFG.read_text(encoding="utf-8"))
    assert cfg["mode"] == "SHADOW_ONLY_NO_ORDERS"
    assert cfg["discovery_cutoff"] == "2026-10-14"
    assert cfg["prospective_start_after"] == "2026-10-14"
    assert [c["id"] for c in cfg["candidates"]] == [
        "H09A_PUT_FLOW_MIRROR_V01",
        "H09B_PUT_FLOW_MIRROR_RISKOFF_V01",
    ]


def test_h09a_and_h09b_logic():
    cfg = json.loads(CFG.read_text(encoding="utf-8"))
    row = {
        "d_atm_iv_prev": 0.01,
        "d_put_call_iv_skew_prev": 0.002,
        "d_put_call_volume_ratio_1pct_prev": -0.1,
        "spy_from_open": -0.003,
        "qqq_from_open": -0.004,
        "iwm_from_open": -0.005,
    }
    assert active_candidates(cfg, row) == [
        "H09A_PUT_FLOW_MIRROR_V01",
        "H09B_PUT_FLOW_MIRROR_RISKOFF_V01",
    ]
    row["iwm_from_open"] = 0.001
    assert active_candidates(cfg, row) == ["H09A_PUT_FLOW_MIRROR_V01"]


def test_live_deltas_are_causal():
    prev = {"atm_iv": 0.20, "put_call_iv_skew": 0.01, "put_call_volume_ratio_1pct": 1.20}
    cur = {"atm_iv": 0.22, "put_call_iv_skew": 0.02, "put_call_volume_ratio_1pct": 1.00}
    row = live_delta_row(prev, cur)
    assert abs(row["d_atm_iv_prev"] - 0.02) < 1e-12
    assert abs(row["d_put_call_iv_skew_prev"] - 0.01) < 1e-12
    assert abs(row["d_put_call_volume_ratio_1pct_prev"] + 0.20) < 1e-12


def test_episode_gap():
    assert not is_new_episode("2026-10-15T14:00:00+00:00", "2026-10-15T14:06:00+00:00", 6)
    assert is_new_episode("2026-10-15T14:00:00+00:00", "2026-10-15T14:06:01+00:00", 6)


def test_summary_adds_one_contract_pnl():
    rows=[
        {"candidate_id":"X","captured_at_utc":"2026-10-16T14:00:00+00:00","put_entry_ask":2.0,"put_ret_60m":0.10,"put_mfe_60m":0.20,"put_mae_60m":-0.05,"put_60m_tp10_sl10":"TP_FIRST"},
        {"candidate_id":"X","captured_at_utc":"2026-10-16T14:10:00+00:00","put_entry_ask":1.5,"put_ret_60m":-0.20,"put_mfe_60m":0.05,"put_mae_60m":-0.30,"put_60m_tp10_sl10":"SL_FIRST"},
    ]
    out=summarize(rows,"X",(60,))["horizons"]["60"]
    assert out["pnl_1_contract_n"] == 2
    assert abs(out["total_pnl_1_contract"] + 10.0) < 1e-9
    assert abs(out["mean_pnl_1_contract"] + 5.0) < 1e-9
    assert abs(out["mean_mfe_pnl_1_contract"] - 23.75) < 1e-9
    assert abs(out["mean_mae_pnl_1_contract"] + 27.5) < 1e-9
    assert abs(out["max_drawdown_pnl_1_contract"] + 30.0) < 1e-9
