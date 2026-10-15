from options_system.h01_path_telemetry import record_path_checkpoints


def test_records_first_observation_at_or_after_checkpoint_only_once():
    p = {}
    assert record_path_checkpoints(p, elapsed_seconds=14, bid=1.0, return_pct=-.01, quote_time="q0", mark_time="m0") == 0
    assert record_path_checkpoints(p, elapsed_seconds=31, bid=.95, return_pct=-.05, quote_time="q1", mark_time="m1") == 2
    assert set(p["path_checkpoints"]) == {"15s", "30s"}
    assert p["path_checkpoints"]["15s"]["observed_elapsed_seconds"] == 31
    assert record_path_checkpoints(p, elapsed_seconds=46, bid=1.05, return_pct=.05, quote_time="q2", mark_time="m2") == 0
    assert record_path_checkpoints(p, elapsed_seconds=61, bid=1.08, return_pct=.08, quote_time="q3", mark_time="m3") == 1
    assert p["path_checkpoints"]["60s"]["return"] == .08
