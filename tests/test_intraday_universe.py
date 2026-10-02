from options_system.intraday_universe import INTRADAY_UNIVERSE,INTRADAY_HORIZONS_MIN

def test_intraday_universe_and_horizons():
    assert "SPY" in INTRADAY_UNIVERSE
    assert "AAPL" in INTRADAY_UNIVERSE
    assert "TSLA" in INTRADAY_UNIVERSE
    assert INTRADAY_HORIZONS_MIN==(5,15,30,60)
