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
            "capital_utilization_pct": (deployed / before) if before > 0 else 0.0,
            "trade_gross_pnl": gross,
            "trade_fees": fees,
            "trade_net_pnl": net,
            "cash_after_trade": cash,
        })
        equity.append(cash)
    executed = [x for x in ledger if x["sizing_status"] == "EXECUTED"]
    wins = sum(x["trade_net_pnl"] > 0 for x in executed)
    losses = sum(x["trade_net_pnl"] < 0 for x in executed)
    pnls = [x["trade_net_pnl"] for x in executed]
    utilizations = [x["capital_utilization_pct"] for x in executed]
    gross_profit = sum(x for x in pnls if x > 0)
    gross_loss = -sum(x for x in pnls if x < 0)
    max_loss_streak = streak = 0
    for x in pnls:
        streak = streak + 1 if x < 0 else 0
        max_loss_streak = max(max_loss_streak, streak)
    max_utilization = max(utilizations, default=0.0)
    risk_band = "NO_DATA" if not executed else ("LOW" if max_utilization <= .25 else "MODERATE" if max_utilization <= .50 else "HIGH" if max_utilization <= .75 else "VERY_HIGH")
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
        "avg_capital_utilization_pct": sum(utilizations) / len(utilizations) if utilizations else 0.0,
        "max_capital_utilization_pct": max_utilization,
        "largest_win": max(pnls, default=0.0),
        "largest_loss": min(pnls, default=0.0),
        "expectancy_per_trade": sum(pnls) / len(pnls) if pnls else None,
        "profit_factor": (gross_profit / gross_loss) if gross_loss > 0 else (None if gross_profit == 0 else "INF"),
        "max_consecutive_losses": max_loss_streak,
        "risk_band": risk_band,
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
