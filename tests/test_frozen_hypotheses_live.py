from datetime import datetime, timedelta, timezone

from options_system.frozen_live_engine import (
    add_previous_deltas,
    episode_activation,
    live_hypothesis_active,
    open_reference_stable,
)


def test_open_reference_guard_requires_two_equal_captures():
    current = {"decision_date": "2026-10-15", "open_refs": {"SPY": 770, "QQQ": 730, "IWM": 270}}
    assert open_reference_stable(None, current)[0] is False
    previous = {"decision_date": "2026-10-15", "open_refs": {"SPY": 770, "QQQ": 730, "IWM": 270}}
    assert open_reference_stable(previous, current) == (True, "STABLE")


def test_open_reference_guard_rejects_changed_provider_open():
    previous = {"decision_date": "2026-10-15", "open_refs": {"SPY": 772, "QQQ": 731, "IWM": 273}}
    current = {"decision_date": "2026-10-15", "open_refs": {"SPY": 770, "QQQ": 730, "IWM": 270}}
    ok, reason = open_reference_stable(previous, current)
    assert ok is False
    assert "UNSTABLE" in reason


def test_h03_is_blocked_only_by_data_quality_guard():
    h03 = {"id": "H03_CALL_RELATIVE_WEAKNESS_REVERSAL_V01", "rules": [
        {"feature": "iwm_from_open", "op": "<=", "value": -0.0033},
        {"feature": "spy_from_open", "op": "<=", "value": -0.0021},
    ]}
    row = {"iwm_from_open": -0.01, "spy_from_open": -0.005}
    assert live_hypothesis_active(h03, row, h03_open_stable=False)[0] is False
    assert live_hypothesis_active(h03, row, h03_open_stable=True)[0] is True


def test_h01_previous_deltas_match_frozen_rule_direction():
    previous = {"atm_iv": 0.10, "put_call_iv_skew": 0.01, "put_call_volume_ratio_1pct": 0.90}
    row = add_previous_deltas({"atm_iv": 0.11, "put_call_iv_skew": 0.005, "put_call_volume_ratio_1pct": 1.10}, previous)
    h01 = {"id": "CALL_FLOW_REVERSAL_V01", "rules": {
        "d_atm_iv_prev_gt": 0.0,
        "d_put_call_iv_skew_prev_lt": 0.0,
        "d_put_call_volume_ratio_1pct_prev_gt": 0.0,
    }}
    assert live_hypothesis_active(h01, row, h03_open_stable=True)[0] is True


def test_episode_policy_matches_six_minute_grouping():
    h = {"id": "CALL_FLOW_REVERSAL_V01", "episode_policy": {"gap_minutes": 6}}
    t0 = datetime(2026, 10, 15, 13, 30, tzinfo=timezone.utc)
    row1 = {"decision_date": "2026-10-15", "captured_at_utc": t0.isoformat()}
    state, sid1 = episode_activation(None, h, row1)
    assert sid1.endswith(":P1")
    row2 = {"decision_date": "2026-10-15", "captured_at_utc": (t0 + timedelta(minutes=5)).isoformat()}
    state, sid2 = episode_activation(state, h, row2)
    assert sid2 is None
    row3 = {"decision_date": "2026-10-15", "captured_at_utc": (t0 + timedelta(minutes=12)).isoformat()}
    state, sid3 = episode_activation(state, h, row3)
    assert sid3.endswith(":P2")


def test_episode_counter_resets_each_session():
    h = {"id": "PUT_SKEW_SHORT_V01"}
    state, sid1 = episode_activation(None, h, {"decision_date": "2026-10-15", "captured_at_utc": "2026-10-15T14:00:00+00:00"})
    assert sid1.endswith(":P1")
    state, sid2 = episode_activation(state, h, {"decision_date": "2026-10-16", "captured_at_utc": "2026-10-16T14:00:00+00:00"})
    assert sid2.endswith(":P1")
