import pytest
from datetime import datetime, timedelta, timezone

from options_system.sl_first_recovery import analyze_episode, summarize

CFG = {
    "sl_touch_return": -0.10,
    "post_sl_targets": [0.10, 0.20, 0.30],
    "horizon_completion_tolerance_minutes": 6,
    "variants": {
        "RECLAIM8": {"reclaim_return": -0.08},
        "REBOUND5": {"rebound_points": 0.05},
    },
}


def point(t0, minute, bid, ask=None):
    return {"time": t0 + timedelta(minutes=minute), "bid": bid, "ask": bid + 0.02 if ask is None else ask}


def test_detects_sl_then_recovery_and_delayed_entries_causally():
    t0 = datetime(2026, 10, 16, 14, 0, tzinfo=timezone.utc)
    pts = [
        point(t0, 0, .98, 1.00),
        point(t0, 1, .89, .91),       # SL10 touched
        point(t0, 2, .82, .84),       # running min
        point(t0, 3, .88, .90),       # rebound +6pp and reclaim8 not yet
        point(t0, 4, .93, .95),
        point(t0, 5, 1.12, 1.14),     # post-SL +10
        point(t0, 6, 1.22, 1.24),     # +20
        point(t0, 7, 1.32, 1.34),     # +30
    ]
    out = analyze_episode(strategy="X", source="T", evidence="TEST", symbol="SPY", side="PUT",
                          signal_time=t0, contract="X", initial_ask=1.0, horizon_minutes=10,
                          points=pts, config=CFG)
    assert out["touched_sl10"] is True
    assert out["post_sl_hit_10"] and out["post_sl_hit_20"] and out["post_sl_hit_30"]
    assert out["post_sl_min_return"] == pytest.approx(-0.18)
    assert out["variants"]["TOUCH10"]["entry_time"] == pts[1]["time"].isoformat()
    assert out["variants"]["RECLAIM8"]["entry_time"] == pts[4]["time"].isoformat()
    assert out["variants"]["REBOUND5"]["entry_time"] == pts[3]["time"].isoformat()


def test_same_mae_mfe_can_have_different_order():
    t0 = datetime(2026, 10, 16, 14, 0, tzinfo=timezone.utc)
    sl_first = [point(t0,0,.98,1), point(t0,1,.85,.87), point(t0,2,1.30,1.32)]
    tp_first = [point(t0,0,.98,1), point(t0,1,1.30,1.32), point(t0,2,.85,.87)]
    a = analyze_episode(strategy="X",source="T",evidence="T",symbol="SPY",side="PUT",signal_time=t0,contract="X",initial_ask=1,horizon_minutes=5,points=sl_first,config=CFG)
    b = analyze_episode(strategy="X",source="T",evidence="T",symbol="SPY",side="PUT",signal_time=t0,contract="X",initial_ask=1,horizon_minutes=5,points=tp_first,config=CFG)
    assert a["mae"] == pytest.approx(-0.15)
    assert b["mae"] == pytest.approx(-0.15)
    assert a["mfe"] == pytest.approx(0.30)
    assert b["mfe"] == pytest.approx(0.30)
    assert a["post_sl_hit_20"] is True
    assert b["post_sl_hit_20"] is False


def test_summary_reports_conditional_recovery_and_replay():
    t0 = datetime(2026, 10, 16, 14, 0, tzinfo=timezone.utc)
    pts = [point(t0,0,.98,1),point(t0,1,.89,.91),point(t0,2,.80,.82),point(t0,3,.90,.92),point(t0,4,1.20,1.22)]
    e = analyze_episode(strategy="X",source="T",evidence="T",symbol="SPY",side="PUT",signal_time=t0,contract="X",initial_ask=1,horizon_minutes=5,points=pts,config=CFG)
    s = summarize([e])
    assert s["touched_sl10"] == 1
    assert s["sl10_then_10_rate"] == 1.0
    assert s["sl10_then_20_rate"] == 1.0
    assert s["variants"]["REBOUND5"]["entries"] == 1


def test_incomplete_horizon_is_not_evaluable():
    t0 = datetime(2026, 10, 16, 14, 0, tzinfo=timezone.utc)
    pts = [point(t0,0,.98,1), point(t0,10,.85,.87)]
    out = analyze_episode(strategy="X",source="T",evidence="T",symbol="SPY",side="PUT",signal_time=t0,contract="X",initial_ask=1,horizon_minutes=60,points=pts,config=CFG)
    assert out["path_available"] is True
    assert out["horizon_complete"] is False
    assert out["evaluable"] is False
