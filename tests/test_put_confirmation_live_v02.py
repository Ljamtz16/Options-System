from datetime import datetime, timedelta, timezone

from options_system.put_confirmation_live import (
    apply_h06_activation,
    h06_match,
    snapshot_to_live_row,
)


def row(ts, spot, spy=-0.001, qqq=-0.002, iwm=-0.001):
    return {
        "captured_at_utc": ts.isoformat(),
        "decision_date": "2026-10-14",
        "spot": spot,
        "spy_from_open": spy,
        "qqq_from_open": qqq,
        "iwm_from_open": iwm,
        "put_contract": "SPY261014P00780000",
        "put_entry_bid": 1.99,
        "put_entry_ask": 2.00,
        "put_entry_bid_size": 10,
        "put_entry_ask_size": 10,
    }


def v02():
    return {
        "state_machine": {
            "confirmation_min_minutes": 6,
            "confirmation_max_minutes": 15,
            "post_signal_lock_minutes": 15,
        }
    }


def test_h06_matches_new_15m_low_with_bearish_5m_impulse():
    t0 = datetime(2026, 10, 14, 14, 0, tzinfo=timezone.utc)
    history = [row(t0 + timedelta(minutes=i), 780.0 - 0.04 * i) for i in range(6)]
    current = row(t0 + timedelta(minutes=6), 779.20)
    matched, reason = h06_match(current, history)
    assert matched is True
    assert reason == "MATCH"


def test_confirmation_requires_all_three_cross_market_series_to_worsen():
    t0 = datetime(2026, 10, 14, 14, 0, tzinfo=timezone.utc)
    machine = {"status": "IDLE", "arm": None, "locked_until_utc": None}
    arm = row(t0, 779.0, spy=-0.0010, qqq=-0.0020, iwm=-0.0010)
    event, signal = apply_h06_activation(machine, arm, v02())
    assert event["event"] == "ARMED"
    assert signal is None

    bad = row(t0 + timedelta(minutes=8), 778.0, spy=-0.0020, qqq=-0.0030, iwm=-0.0005)
    event, signal = apply_h06_activation(machine, bad, v02())
    assert event["event"] == "CONFIRM_REJECT_ALL3"
    assert signal is None
    assert machine["arm"]["captured_at_utc"] == arm["captured_at_utc"]

    good = row(t0 + timedelta(minutes=9), 777.8, spy=-0.0021, qqq=-0.0032, iwm=-0.0015)
    event, signal = apply_h06_activation(machine, good, v02())
    assert event["event"] == "CONFIRMED"
    assert signal is not None
    assert machine["status"] == "LOCKED"
    assert 6 <= signal["confirmation_gap_minutes"] <= 15


def test_raw_snapshot_converts_to_same_live_contract_fields():
    envelope = {
        "captured_at_utc": "2026-10-14T14:00:00+00:00",
        "capture_id": "abc123",
        "payload": {
            "research_state": {"features": {"decision_date": "2026-10-14"}},
            "underlying": {"snapshot": {"latestTrade": {"p": 780.0}}},
            "cross_market": {"features": {
                "spy_from_open": -0.001,
                "qqq_from_open": -0.002,
                "iwm_from_open": -0.003,
            }},
            "options": {"snapshot": {"snapshots": {
                "SPY261014P00780000": {
                    "greeks": {"delta": -0.50},
                    "latestQuote": {"bp": 1.99, "ap": 2.01, "bs": 10, "as": 11},
                    "impliedVolatility": 0.20,
                },
                "SPY261014C00780000": {
                    "greeks": {"delta": 0.50},
                    "latestQuote": {"bp": 2.10, "ap": 2.12, "bs": 12, "as": 13},
                    "impliedVolatility": 0.19,
                },
            }}},
        },
    }
    out = snapshot_to_live_row(envelope)
    assert out["put_contract"] == "SPY261014P00780000"
    assert out["put_entry_bid"] == 1.99
    assert out["put_entry_ask"] == 2.01
    assert out["iwm_from_open"] == -0.003
