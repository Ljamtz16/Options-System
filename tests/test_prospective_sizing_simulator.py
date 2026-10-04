import pytest
from options_system.option_costs import one_contract_trade
from options_system.prospective_episode_tracker import build_virtual_account
from options_system.prospective_sizing_simulator import simulate_strategy, compare_sizing

def ep(day, start, ask=2.50, ret=.10, outcome="TP_FIRST"):
    return {
        "decision_date": day, "start": start, "tp_sl": outcome,
        "trade_1_contract": one_contract_trade(ask, ret),
    }

def test_fixed_one_contract_reproduces_official_account():
    episodes=[ep("2026-10-05","2026-10-05T14:00:00+00:00",2,.10),
              ep("2026-10-05","2026-10-05T15:00:00+00:00",2.5,-.10,"SL_FIRST")]
    official=build_virtual_account(episodes,1000)
    sim=simulate_strategy(episodes,{"mode":"fixed","contracts":1},1000,"fixed")
    assert sim["final_cash"] == pytest.approx(official["final_cash"])
    assert [x["trade_net_pnl"] for x in sim["ledger"]] == pytest.approx([x["trade_net_pnl"] for x in official["ledger"]])

def test_pct_20_can_skip_when_budget_cannot_buy_one_contract():
    sim=simulate_strategy([ep("2026-10-05","2026-10-05T14:00:00+00:00",2.5,.10)],
                          {"mode":"pct","fraction":.20},1000)
    assert sim["ledger"][0]["contracts"] == 0
    assert sim["ledger"][0]["sizing_status"] == "SKIP_INSUFFICIENT_SIZING_BUDGET"
    assert sim["final_cash"] == 1000

def test_pct_80_can_buy_multiple_whole_contracts():
    sim=simulate_strategy([ep("2026-10-05","2026-10-05T14:00:00+00:00",2.5,.10)],
                          {"mode":"pct","fraction":.80},1000)
    assert sim["ledger"][0]["contracts"] == 3
    assert sim["ledger"][0]["capital_deployed"] == pytest.approx(750)

def test_sequential_compounding_changes_next_sizing():
    episodes=[ep("2026-10-05","2026-10-05T14:00:00+00:00",2.5,1.0),
              ep("2026-10-05","2026-10-05T15:00:00+00:00",2.5,.10)]
    sim=simulate_strategy(episodes,{"mode":"pct","fraction":.80},1000)
    assert sim["ledger"][0]["contracts"] == 3
    assert sim["ledger"][1]["cash_before_trade"] == pytest.approx(sim["ledger"][0]["cash_after_trade"])
    assert sim["ledger"][1]["contracts"] > sim["ledger"][0]["contracts"]

def test_pending_has_no_cash_impact():
    e=ep("2026-10-05","2026-10-05T14:00:00+00:00")
    e["trade_1_contract"]=None
    sim=simulate_strategy([e],{"mode":"pct","fraction":.80},1000)
    assert sim["ledger"][0]["sizing_status"] == "PENDING_OUTCOME"
    assert sim["final_cash"] == 1000

def test_drawdown_uses_running_equity_peak():
    episodes=[ep("2026-10-05","2026-10-05T14:00:00+00:00",1,.10),
              ep("2026-10-05","2026-10-05T15:00:00+00:00",1,-.50,"SL_FIRST")]
    sim=simulate_strategy(episodes,{"mode":"fixed","contracts":1},1000)
    peak=sim["ledger"][0]["cash_after_trade"]
    trough=sim["ledger"][1]["cash_after_trade"]
    assert sim["max_drawdown_pct"] == pytest.approx((peak-trough)/peak)

def test_comparison_has_all_governed_strategies():
    c=compare_sizing([],1000)
    assert set(c["strategies"]) == {"fixed_1_contract","pct_20","pct_40","pct_60","pct_80"}
    assert c["scientific_evidence"] is False
    assert all(v["final_cash"] == 1000 for v in c["strategies"].values())


def test_risk_metrics_and_loss_streak():
    episodes=[ep("2026-10-05","2026-10-05T14:00:00+00:00",1,.10),
              ep("2026-10-05","2026-10-05T15:00:00+00:00",1,-.10,"SL_FIRST"),
              ep("2026-10-05","2026-10-05T16:00:00+00:00",1,-.10,"SL_FIRST")]
    sim=simulate_strategy(episodes,{"mode":"fixed","contracts":1},1000)
    assert sim["executed_trades"] == 3
    assert sim["max_consecutive_losses"] == 2
    assert sim["largest_win"] > 0
    assert sim["largest_loss"] < 0
    assert sim["expectancy_per_trade"] == pytest.approx(sim["net_pnl"]/3)
    assert sim["profit_factor"] > 0
    assert sim["max_capital_utilization_pct"] > 0
    assert sim["risk_band"] == "LOW"

def test_percentage_risk_band_reflects_actual_integer_contract_exposure():
    sim=simulate_strategy([ep("2026-10-05","2026-10-05T14:00:00+00:00",2.5,.10)],
                          {"mode":"pct","fraction":.80},1000)
    assert sim["ledger"][0]["capital_utilization_pct"] == pytest.approx(.75)
    assert sim["max_capital_utilization_pct"] == pytest.approx(.75)
    assert sim["risk_band"] == "HIGH"

def test_empty_strategy_risk_metrics_are_neutral():
    sim=simulate_strategy([],{"mode":"pct","fraction":.80},1000)
    assert sim["risk_band"] == "NO_DATA"
    assert sim["max_capital_utilization_pct"] == 0
    assert sim["expectancy_per_trade"] is None
    assert sim["profit_factor"] is None
