from dataclasses import dataclass

@dataclass(frozen=True)
class LiquidityPolicy:
    min_bid: float = 0.05
    max_ask: float = 50.0
    max_spread_pct: float = 0.20
    min_bid_size: int = 1
    min_ask_size: int = 1
    delta_abs_min: float = 0.20
    delta_abs_max: float = 0.80


def evaluate_liquidity(contract, policy=LiquidityPolicy()):
    if not contract:
        return {"pass": False, "reason": "NO_CONTRACT"}
    bid = contract.get("bid")
    ask = contract.get("ask")
    delta = contract.get("delta")
    if bid is None or ask is None or bid <= 0 or ask <= 0 or ask < bid:
        return {"pass": False, "reason": "INVALID_QUOTE"}
    mid = (float(bid) + float(ask)) / 2
    spread_pct = (float(ask) - float(bid)) / mid if mid > 0 else None
    if float(bid) < policy.min_bid or float(ask) > policy.max_ask:
        return {"pass": False, "reason": "PRICE_BOUNDS", "spread_pct": spread_pct}
    if spread_pct is None or spread_pct > policy.max_spread_pct:
        return {"pass": False, "reason": "SPREAD", "spread_pct": spread_pct}
    if delta is None or not (policy.delta_abs_min <= abs(float(delta)) <= policy.delta_abs_max):
        return {"pass": False, "reason": "DELTA_RANGE", "spread_pct": spread_pct}
    bs = contract.get("bid_size")
    asks = contract.get("ask_size")
    if bs is not None and int(bs) < policy.min_bid_size:
        return {"pass": False, "reason": "BID_SIZE", "spread_pct": spread_pct}
    if asks is not None and int(asks) < policy.min_ask_size:
        return {"pass": False, "reason": "ASK_SIZE", "spread_pct": spread_pct}
    return {"pass": True, "reason": "PASS", "spread_pct": spread_pct}
