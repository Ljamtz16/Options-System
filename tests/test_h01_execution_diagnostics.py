from options_system.h01_execution_diagnostics import policy_return, session_bucket, stop_summary


def test_policy_return_respects_tp_and_stop_thresholds():
    tp = {"call_60m_tp10_sl20": "TP_FIRST", "call_ret_60m": "0.50"}
    sl = {"call_60m_tp10_sl20": "SL_FIRST", "call_ret_60m": "0.50"}
    neither = {"call_60m_tp10_sl20": "NEITHER", "call_ret_60m": "0.03"}
    assert policy_return(tp, 60, 20) == 0.10
    assert policy_return(sl, 60, 20) == -0.20
    assert policy_return(neither, 60, 20) == 0.03


def test_stop_summary_counts_path_order():
    rows = [
        {"call_60m_tp10_sl10": "TP_FIRST", "call_ret_60m": "0.20"},
        {"call_60m_tp10_sl10": "SL_FIRST", "call_ret_60m": "0.20"},
        {"call_60m_tp10_sl10": "NEITHER", "call_ret_60m": "0.02"},
    ]
    out = stop_summary(rows, 60, 10)
    assert out["tp_first"] == 1
    assert out["sl_first"] == 1
    assert out["neither"] == 1


def test_session_bucket_uses_new_york_time():
    assert session_bucket("2026-10-15T14:00:00+00:00") == "09:30-11:00"
    assert session_bucket("2026-10-15T16:30:00+00:00") == "11:00-14:00"
    assert session_bucket("2026-10-15T19:00:00+00:00") == "14:00-16:00"
