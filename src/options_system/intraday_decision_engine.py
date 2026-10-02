ALLOWED_HORIZONS = (15, 30, 60)


def intraday_research_decision(
    horizon_min,
    state_supported,
    direction_supported,
    direction,
    directional_edge,
    liquidity_pass,
    expected_return=None,
    robust=False,
    min_direction_edge=0.05,
    min_expected_return=0.0,
):
    if horizon_min not in ALLOWED_HORIZONS:
        return {"decision": "NO_TRADE_HORIZON", "candidate": False}
    if not state_supported:
        return {"decision": "NO_TRADE_STATE", "candidate": False}
    if (not direction_supported or direction not in ("UP", "DOWN")
            or abs(float(directional_edge or 0)) < min_direction_edge):
        return {"decision": "NO_TRADE_DIRECTION", "candidate": False}
    if not liquidity_pass:
        return {"decision": "NO_TRADE_LIQUIDITY", "candidate": False}
    if expected_return is None or float(expected_return) <= min_expected_return:
        return {"decision": "NO_TRADE_EV", "candidate": False}
    if not robust:
        return {"decision": "NO_TRADE_STRESS", "candidate": False}
    side = "CALL" if direction == "UP" else "PUT"
    return {
        "decision": f"RESEARCH_{side}_CANDIDATE",
        "candidate": True,
        "side": side,
        "horizon_min": horizon_min,
        "directional_edge": float(directional_edge),
        "expected_return": float(expected_return),
    }
