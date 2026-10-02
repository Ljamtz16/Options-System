from src.options_system.multimonth_orchestrator import utc_stamp
def test_dst_conversion():
    assert utc_stamp("2024-02-01","09:30").endswith("14:30:00Z")
    assert utc_stamp("2024-03-11","09:30").endswith("13:30:00Z")
