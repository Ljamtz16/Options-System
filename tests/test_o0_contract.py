from src.options_system import settings


def test_underlying_is_spy_only():
    assert settings.UNDERLYING == "SPY"


def test_only_long_call_put_scope():
    assert settings.ALLOWED_OPTION_SIDES == ("call", "put")


def test_no_trade_is_default():
    assert settings.DEFAULT_DECISION == "NO_TRADE"


def test_execution_is_locked():
    assert settings.LIVE_TRADING_ENABLED is False
    assert settings.PAPER_TRADING_ENABLED is False
