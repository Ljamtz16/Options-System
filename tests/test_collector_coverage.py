import json

from options_system.collector_coverage import record_collector_event


def test_coverage_counts_success_failure_and_armed_gap(tmp_path):
    summary = tmp_path / "summary.json"
    events = tmp_path / "events.jsonl"
    record_collector_event(summary, events, {
        "decision_date": "2026-10-15", "success": True,
        "put_machine_status": "IDLE", "error_type": None,
    })
    record_collector_event(summary, events, {
        "decision_date": "2026-10-15", "success": False,
        "put_machine_status": "ARMED", "error_type": "TIMEOUT",
    })
    data = json.loads(summary.read_text())
    day = data["days"]["2026-10-15"]
    assert day["attempts"] == 2
    assert day["successes"] == 1
    assert day["failures"] == 1
    assert day["armed_failures"] == 1
    assert day["failure_types"] == {"TIMEOUT": 1}
    assert day["coverage_rate"] == 0.5
    assert len(events.read_text().splitlines()) == 2
