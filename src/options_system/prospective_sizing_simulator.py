import math
from options_system.option_costs import daily_regulatory_fees

DEFAULT_STRATEGIES = {
    "fixed_1_contract": {"mode": "fixed", "contracts": 1},
    "pct_20": {"mode": "pct", "fraction": 0.20},
    "pct_40": {"mode": "pct", "fraction": 0.40},
    "pct_60": {"mode": "pct", "fraction": 0.60},
    "pct_80": {"mode": "pct", "fraction": 0.80},
}

def _contracts_for(strategy, cash, capital_per_contract):
    if not capital_per_contract or capital_per_contract <= 0:
        return 0
    if strategy["mode"] == "fixed":
        n = int(strategy.get("contracts", 1))
        return n if n * capital_per_contract <= cash else 0
    budget = cash * float(strategy["fraction"])
    return max(0, math.floor((budget + 1e-12) / capital_per_contract))

def _max_drawdown(equity):
    peak = equity[0] if equity else 0.0
    worst = 0.0
    for value in equity:
        peak = max(peak, value)
        if peak > 0:
            worst = max(worst, (peak - value) / peak)
    return worst

def simulate_strategy(episodes, strategy, initial_cash=1000.0, name="strategy"):
    cash = float(initial_cash)
    ledger = []
    equity = [cash]
    ordered = sorted(episodes, key=lambda e: (e.get("decision_date", ""), e.get("start", "")))
    for e in ordered:
        before = cash
        t = e.get("trade_1_contract")
        contracts = 0
        gross = fees = net = deployed = 0.0
        if not t:
            status = "PENDING_OUTCOME"
        else:
            cap = float(t["capital_required"])
            contracts = _contracts_for(strategy, cash, cap)
            if contracts < 1:
                status = "SKIP_INSUFFICIENT_SIZING_BUDGET"
            else:
                status = "EXECUTED"
                deployed = cap * contracts
                gross = float(t["gross_pnl"]) * contracts
                fees = float(daily_regulatory_fees([t] * contracts)["total"])
                net = gross - fees
                cash += net
        ledger.append({
            **e,
            "sizing_status": status,
            "cash_before_trade": before,
            "contracts": contracts,
            "capital_deployed": deployed,
            "trade_gross_pnl": gross,
            "trade_fees": fees,
            "trade_net_pnl": net,
            "cash_after_trade": cash,
        })
        equity.append(cash)
    executed = [x for x in ledger if x["sizing_status"] == "EXECUTED"]
    wins = sum(x["trade_net_pnl"] > 0 for x in executed)
    losses = sum(x["trade_net_pnl"] < 0 for x in executed)
    return {
        "strategy": name,
        "initial_cash": float(initial_cash),
        "final_cash": cash,
        "net_pnl": cash - float(initial_cash),
        "return_pct": (cash / float(initial_cash) - 1.0) if initial_cash else 0.0,
        "max_drawdown_pct": _max_drawdown(equity),
        "executed_trades": len(executed),
        "wins": wins,
        "losses": losses,
        "win_rate": wins / len(executed) if executed else None,
        "max_contracts": max((x["contracts"] for x in ledger), default=0),
        "ledger": ledger,
    }

def compare_sizing(episodes, initial_cash=1000.0, strategies=None):
    strategies = strategies or DEFAULT_STRATEGIES
    return {
        "initial_cash": float(initial_cash),
        "scientific_evidence": False,
        "purpose": "execution_and_risk_simulation_only",
        "strategies": {
            name: simulate_strategy(episodes, cfg, initial_cash, name)
            for name, cfg in strategies.items()
        },
    }
