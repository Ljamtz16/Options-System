from copy import deepcopy

from options_system.signal_episode_engine import apply_activation, apply_meta_decision


def cfg():
    return {
        "episode_gap_minutes": 15,
        "flicker_window_minutes": 30,
        "ttt": {
            "H01": {"mode": "FIRST_CLEAN_META", "min_observations": 1, "window_minutes": 15, "max_flips": 0},
            "H09": {"mode": "ACTIVATION_2_OF_3", "min_observations": 2, "window_minutes": 10, "max_flips": 0},
            "MULTI": {"mode": "ACTIVATION_2_OF_3", "min_observations": 2, "window_minutes": 10, "max_flips": 0},
        },
        "hysteresis": {"confirmation_memory_minutes": 15},
    }


def state():
    return {"active_episodes": {}, "recent_episodes": [], "episode_sequences": {}, "direction_memory": {}}


def meta(source="H01", symbol="SPY", side="CALL", decision="ACCEPT", time="2026-10-16T14:00:00+00:00"):
    return {
        "source": source, "symbol": symbol, "side": side, "decision": decision,
        "time": time, "meta_decision_id": f"m:{source}:{time}", "strategy": "S",
        "block_reasons": ["x"] if decision == "BLOCK" else [],
        "wait_reasons": ["w"] if decision == "WAIT" else [],
    }


def activation(source="H09", symbol="SPY", side="PUT", time="2026-10-16T14:00:00+00:00", candidate="H09B"):
    return {"source": source, "symbol": symbol, "side": side, "signal_time": time, "candidate_id": candidate}


def test_h01_first_clean_meta_confirms_once():
    s = state()
    ep = apply_activation(s, activation("H01", "SPY", "CALL", candidate="H01"), cfg())
    assert ep["shadow_decision"] == "WAIT"
    ep = apply_meta_decision(s, meta(), cfg())
    assert ep["shadow_decision"] == "ACCEPT"
    assert ep["ttt_state"] == "CONFIRMED_FIRST_CLEAN"
    assert ep["would_authorize_new_trade"] is True
    ep = apply_meta_decision(s, meta(time="2026-10-16T14:05:00+00:00"), cfg())
    assert ep["shadow_decision"] == "ACCEPT"
    assert ep["would_authorize_new_trade"] is False


def test_h09_needs_two_activations_and_accept_meta():
    s = state()
    ep = apply_activation(s, activation(time="2026-10-16T14:00:00+00:00"), cfg())
    assert ep["ttt_state"] == "WAIT_META_DECISION"
    ep = apply_meta_decision(s, meta("H09", "SPY", "PUT", "ACCEPT", "2026-10-16T14:00:05+00:00"), cfg())
    assert ep["shadow_decision"] == "WAIT"
    assert ep["ttt_state"] == "BUILDING"
    ep = apply_activation(s, activation(time="2026-10-16T14:01:00+00:00"), cfg())
    assert ep["shadow_decision"] == "ACCEPT"
    assert ep["ttt_state"] == "CONFIRMED_PERSISTENCE"
    assert ep["would_authorize_new_trade"] is True


def test_meta_wait_is_never_overridden_by_ttt():
    s = state()
    apply_activation(s, activation(time="2026-10-16T14:00:00+00:00"), cfg())
    apply_activation(s, activation(time="2026-10-16T14:01:00+00:00"), cfg())
    ep = apply_meta_decision(s, meta("H09", "SPY", "PUT", "WAIT", "2026-10-16T14:01:05+00:00"), cfg())
    assert ep["shadow_decision"] == "WAIT"
    assert ep["ttt_state"] == "META_WAIT"


def test_block_resets_confirmation_memory():
    s = state()
    apply_activation(s, activation(time="2026-10-16T14:00:00+00:00"), cfg())
    apply_meta_decision(s, meta("H09", "SPY", "PUT", "ACCEPT", "2026-10-16T14:00:05+00:00"), cfg())
    ep = apply_activation(s, activation(time="2026-10-16T14:01:00+00:00"), cfg())
    assert ep["shadow_decision"] == "ACCEPT"
    ep = apply_meta_decision(s, meta("H09", "SPY", "PUT", "BLOCK", "2026-10-16T14:02:00+00:00"), cfg())
    assert ep["shadow_decision"] == "BLOCK"
    assert ep["hysteresis_state"] == "RESET_BY_BLOCK"


def test_new_episode_after_gap():
    s = state()
    a = apply_activation(s, activation(time="2026-10-16T14:00:00+00:00"), cfg())
    b = apply_activation(s, activation(time="2026-10-16T14:20:01+00:00"), cfg())
    assert a["episode_id"] != b["episode_id"]
    assert len(s["recent_episodes"]) == 1


def test_direction_flip_is_recorded():
    s = state()
    apply_activation(s, activation("MULTI", "AAPL", "CALL", "2026-10-16T14:00:00+00:00", "MS02"), cfg())
    ep = apply_activation(s, activation("MULTI", "AAPL", "PUT", "2026-10-16T14:05:00+00:00", "MS01"), cfg())
    assert ep["flip_count_30m"] == 1
