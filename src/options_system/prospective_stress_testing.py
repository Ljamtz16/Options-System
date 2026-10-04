from copy import deepcopy
from options_system.option_costs import one_contract_trade
from options_system.prospective_sizing_simulator import DEFAULT_STRATEGIES, simulate_strategy

DEFAULT_STRESS_SCENARIOS = {
    "loss_streak_2": {"losses": 2, "entry_ask": 2.50, "loss_return": -0.10},
    "loss_streak_3": {"losses": 3, "entry_ask": 2.50, "loss_return": -0.10},
    "loss_streak_5": {"losses": 5, "entry_ask": 2.50, "loss_return": -0.10},
    "expensive_contract_loss_streak_3": {"losses": 3, "entry_ask": 4.00, "loss_return": -0.10},
    "slippage_5c_loss_streak_3": {"losses": 3, "entry_ask": 2.50, "loss_return": -0.10, "slippage_cents_per_leg": 5},
    "slippage_10c_loss_streak_3": {"losses": 3, "entry_ask": 2.50, "loss_return": -0.10, "slippage_cents_per_leg": 10},
}

def _stress_episodes(cfg):
    episodes = []
    for i in range(int(cfg["losses"])):
        t = one_contract_trade(
            cfg["entry_ask"],
            cfg["loss_return"],
            cfg.get("slippage_cents_per_leg", 0),
        )
        # simulate_strategy settles gross less rounded regulatory fees. Slippage
        # therefore belongs in gross P&L for this synthetic stress trade.
        if t and t.get("extra_slippage"):
            t = deepcopy(t)
            t["gross_pnl"] -= float(t["extra_slippage"])
        episodes.append({
            "decision_date": f"STRESS-{i+1:02d}",
            "start": f"STRESS-{i+1:02d}",
            "tp_sl": "SL_FIRST",
            "trade_1_contract": t,
        })
    return episodes

def run_stress_test(initial_cash=1000.0, strategies=None, scenarios=None):
    strategies = strategies or DEFAULT_STRATEGIES
    scenarios = scenarios or DEFAULT_STRESS_SCENARIOS
    results = {}
    for scenario_name, cfg in scenarios.items():
        episodes = _stress_episodes(cfg)
        by_strategy = {}
        for strategy_name, strategy in strategies.items():
            sim = simulate_strategy(episodes, strategy, initial_cash, strategy_name)
            by_strategy[strategy_name] = {
                "final_cash": sim["final_cash"],
                "net_pnl": sim["net_pnl"],
                "return_pct": sim["return_pct"],
                "max_drawdown_pct": sim["max_drawdown_pct"],
                "executed_trades": sim["executed_trades"],
                "max_contracts": sim["max_contracts"],
                "max_capital_utilization_pct": sim["max_capital_utilization_pct"],
                "risk_band": sim["risk_band"],
                "survived": sim["final_cash"] > 0,
            }
        results[scenario_name] = {"config": cfg, "strategies": by_strategy}
    return {
        "initial_cash": float(initial_cash),
        "scientific_evidence": False,
        "purpose": "deterministic_execution_risk_stress_testing_only",
        "scenarios": results,
    }
