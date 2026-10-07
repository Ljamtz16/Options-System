import math

DEFAULT_EXECUTION_POLICY = {
    "max_contract_price": 5.00,
    "max_spread_pct": 0.12,
    "min_bid": 0.01,
    "min_bid_size": 1,
    "min_ask_size": 1,
    "require_market_quality": True,
}

def evaluate_execution(episode, risk_gate, cash=1000.0, policy=None):
    policy = {**DEFAULT_EXECUTION_POLICY, **(policy or {})}
    allowed = float((risk_gate or {}).get("allowed_max_fraction") or 0.0)
    if not math.isfinite(allowed) or not 0 <= allowed <= 1 or not math.isfinite(float(cash)) or float(cash) < 0:
        return dict(status='BLOCK',executable=False,reasons=['INVALID_RISK_BUDGET'],missing_market_quality=[],
                    contract=episode.get('contract'),entry_ask=None,capital_per_contract=None,
                    risk_budget=0.,max_contracts_by_risk_budget=0,market_quality={},policy=policy)
    reasons = []
    missing = []
    contract = episode.get("contract")
    ask = episode.get("entry_ask")
    bid = episode.get("entry_bid")
    bid_size = episode.get("entry_bid_size")
    ask_size = episode.get("entry_ask_size")

    if (risk_gate or {}).get("status") == "BLOCKED" or allowed <= 0:
        reasons.append("RISK_GATE_BLOCKED")
    if not contract:
        reasons.append("NO_CONTRACT")
    try:
        ask = float(ask)
    except (TypeError, ValueError):
        ask = None
    if ask is not None and not math.isfinite(ask):ask=None
    if ask is None or ask <= 0:
        reasons.append("INVALID_ASK")
    elif ask > float(policy["max_contract_price"]):
        reasons.append("CONTRACT_PRICE_ABOVE_LIMIT")

    capital_per_contract = ask * 100.0 if ask else None
    budget = float(cash) * allowed
    max_contracts = int(budget // capital_per_contract) if capital_per_contract else 0
    if capital_per_contract and max_contracts < 1:
        reasons.append("INSUFFICIENT_RISK_BUDGET")

    quality = {}
    if bid in (None, ""):
        missing.append("entry_bid")
    else:
        bid = float(bid)
        quality["bid"] = bid
        if not math.isfinite(bid) or bid < float(policy["min_bid"]):
            reasons.append("BID_BELOW_LIMIT")
            if not math.isfinite(bid):quality['bid']=None
        if ask:
            spread_pct = (ask - bid) / ask
            quality["spread_pct"] = spread_pct if math.isfinite(spread_pct) else None
            if spread_pct < 0:
                reasons.append("CROSSED_OR_INVALID_QUOTE")
            elif spread_pct > float(policy["max_spread_pct"]):
                reasons.append("SPREAD_ABOVE_LIMIT")

    for field, value, minimum in (
        ("entry_bid_size", bid_size, policy["min_bid_size"]),
        ("entry_ask_size", ask_size, policy["min_ask_size"]),
    ):
        if value in (None, ""):
            missing.append(field)
        else:
            quality[field] = float(value) if math.isfinite(float(value)) else None
            if not math.isfinite(float(value)) or float(value) < float(minimum):
                reasons.append(field.upper() + "_BELOW_LIMIT")

    hard_block = bool(reasons)
    if hard_block:
        status = "BLOCK"
    elif missing and policy["require_market_quality"]:
        status = "REVIEW_MISSING_MARKET_QUALITY"
    else:
        status = "PASS"

    return {
        "status": status,
        "executable": status == "PASS",
        "reasons": reasons,
        "missing_market_quality": missing,
        "contract": contract,
        "entry_ask": ask,
        "capital_per_contract": capital_per_contract,
        "risk_budget": budget,
        "max_contracts_by_risk_budget": max_contracts,
        "market_quality": quality,
        "policy": policy,
    }

def evaluate_episodes(episodes, risk_gate, cash=1000.0, policy=None):
    return [dict(e, execution_gate=evaluate_execution(e, risk_gate, cash, policy)) for e in episodes]
