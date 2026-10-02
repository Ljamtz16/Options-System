from src.options_system.market_calendar import regular_session_utc

def test_dst_windows():
    assert regular_session_utc("2026-01-15")==("2026-01-15T14:30:00Z","2026-01-15T21:00:00Z")
    assert regular_session_utc("2026-09-29")==("2026-09-29T13:30:00Z","2026-09-29T20:00:00Z")
