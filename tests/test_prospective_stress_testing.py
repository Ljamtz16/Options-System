import pytest
from options_system.prospective_stress_testing import run_stress_test

def test_stress_report_is_not_scientific_evidence():
    r=run_stress_test()
    assert r["scientific_evidence"] is False
    assert r["purpose"] == "deterministic_execution_risk_stress_testing_only"
    assert len(r["scenarios"]) == 6

def test_more_losses_do_not_improve_same_strategy():
    r=run_stress_test()
    for name in ("fixed_1_contract","pct_20","pct_40","pct_60","pct_80"):
        c2=r["scenarios"]["loss_streak_2"]["strategies"][name]["final_cash"]
        c3=r["scenarios"]["loss_streak_3"]["strategies"][name]["final_cash"]
        c5=r["scenarios"]["loss_streak_5"]["strategies"][name]["final_cash"]
        assert c5 <= c3 <= c2

def test_more_slippage_worsens_three_loss_stress():
    r=run_stress_test()
    for name in ("fixed_1_contract","pct_20","pct_40","pct_60","pct_80"):
        base=r["scenarios"]["loss_streak_3"]["strategies"][name]["final_cash"]
        s5=r["scenarios"]["slippage_5c_loss_streak_3"]["strategies"][name]["final_cash"]
        s10=r["scenarios"]["slippage_10c_loss_streak_3"]["strategies"][name]["final_cash"]
        # Strategies unable to afford a contract are unchanged; executed ones worsen.
        assert s10 <= s5 <= base

def test_aggressive_sizing_has_larger_drawdown_when_both_execute():
    r=run_stress_test()
    s=r["scenarios"]["loss_streak_3"]["strategies"]
    assert s["pct_80"]["max_drawdown_pct"] > s["pct_60"]["max_drawdown_pct"] > s["pct_40"]["max_drawdown_pct"]

def test_expensive_contract_changes_integer_participation():
    r=run_stress_test()
    s=r["scenarios"]["expensive_contract_loss_streak_3"]["strategies"]
    assert s["pct_20"]["executed_trades"] == 0
    assert s["pct_40"]["executed_trades"] >= 1
    assert s["pct_80"]["max_contracts"] >= s["pct_40"]["max_contracts"]

def test_stress_never_uses_fractional_contracts():
    r=run_stress_test()
    for scenario in r["scenarios"].values():
        for result in scenario["strategies"].values():
            assert isinstance(result["max_contracts"], int)
            assert result["max_contracts"] >= 0
