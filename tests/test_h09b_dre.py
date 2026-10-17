from options_system.h09b_dre import route_signal, spread_pct, touch10_triggered

CFG = {
    "buy_now_max_spread_pct": 0.005,
    "arm_touch10_max_spread_pct": 0.0075,
    "arm_trigger_return": -0.10,
}


def test_routes_three_spread_zones():
    assert route_signal(0.996, 1.0, CFG)["decision"] == "BUY_NOW"
    assert route_signal(0.994, 1.0, CFG)["decision"] == "ARM_TOUCH10"
    assert route_signal(0.98, 1.0, CFG)["decision"] == "BLOCK"


def test_invalid_quote_fails_closed():
    assert route_signal(None, 1.0, CFG)["decision"] == "BLOCK"
    assert spread_pct(1.1, 1.0) is None


def test_touch10_is_causal_from_original_ask():
    hit, mark = touch10_triggered(2.00, 1.80, CFG)
    assert hit is True
    assert round(mark, 6) == -0.10
    hit, _ = touch10_triggered(2.00, 1.81, CFG)
    assert hit is False
