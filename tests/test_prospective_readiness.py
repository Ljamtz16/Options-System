import json

from options_system.prospective_readiness import build_health


def put(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj), encoding="utf-8")


def setup_root(root, episodes=None, snapshot_time="2026-10-02T19:55:05+00:00"):
    a = root / "artifacts" / "intraday"

    put(
        a / "FROZEN_HYPOTHESES_V02.json",
        {
            "hypotheses": [
                {
                    "id": "H03_CALL_RELATIVE_WEAKNESS_REVERSAL_V01",
                    "prospective_start_after": "2026-10-02",
                }
            ]
        },
    )

    put(
        a / "PROSPECTIVE_RISK_GATE_V01.json",
        {"status": "ACTIVE", "allowed_max_fraction": 0.2},
    )

    put(
        a / "PROSPECTIVE_EXECUTION_GATE_V01.json",
        {
            "counts": {
                "PASS": 0,
                "BLOCK": 0,
                "REVIEW_MISSING_MARKET_QUALITY": 0,
            }
        },
    )

    put(
        a / "HYPOTHESIS_DAILY_REPORT_V02.json",
        {"prospective_episodes": episodes or []},
    )

    put(a / "research_dashboard_meta.json", {})

    raw = root / "data" / "raw" / "prospective"
    raw.mkdir(parents=True)

    put(
        raw / "spy_options_x.json",
        {"captured_at_utc": snapshot_time},
    )

    return a


def test_waiting_without_post_freeze_market_data(tmp_path):
    setup_root(tmp_path)

    h = build_health(tmp_path)

    assert h["overall_status"] == "WAITING_MARKET_DATA"
    assert h["failures"] == 0
    assert h["post_freeze_snapshot_count"] == 0


def test_post_freeze_data_without_signal_is_valid(tmp_path):
    setup_root(
        tmp_path,
        snapshot_time="2026-10-05T13:35:00+00:00",
    )

    h = build_health(tmp_path)

    assert h["overall_status"] == "DATA_RECEIVED_NO_SIGNAL"
    assert h["failures"] == 0
    assert h["post_freeze_snapshot_count"] == 1
    assert h["prospective_episode_count"] == 0

    evidence = next(
        x for x in h["checks"]
        if x["id"] == "prospective_evidence"
    )
    assert evidence["status"] == "NO_SIGNAL"


def test_ready_after_first_post_freeze_episode(tmp_path):
    setup_root(
        tmp_path,
        episodes=[{"decision_date": "2026-10-05"}],
        snapshot_time="2026-10-05T13:35:00+00:00",
    )

    h = build_health(tmp_path)

    assert h["overall_status"] == "READY"
    assert h["post_freeze_snapshot_count"] == 1
    assert h["prospective_episode_count"] == 1


def test_missing_h03_freeze_is_failure(tmp_path):
    a = setup_root(tmp_path)
    (a / "FROZEN_HYPOTHESES_V02.json").unlink()

    h = build_health(tmp_path)

    assert h["overall_status"] == "NOT_READY"
    assert next(
        x for x in h["checks"]
        if x["id"] == "h03_frozen"
    )["status"] == "FAIL"


def test_blocked_risk_gate_is_valid_operational_state(tmp_path):
    a = setup_root(
        tmp_path,
        episodes=[{"decision_date": "2026-10-05"}],
        snapshot_time="2026-10-05T13:35:00+00:00",
    )

    put(
        a / "PROSPECTIVE_RISK_GATE_V01.json",
        {"status": "BLOCKED", "allowed_max_fraction": 0},
    )

    h = build_health(tmp_path)

    assert next(
        x for x in h["checks"]
        if x["id"] == "risk_gate"
    )["status"] == "PASS"
