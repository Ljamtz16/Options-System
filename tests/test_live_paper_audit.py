from copy import deepcopy

import pytest

from options_system.live_paper_audit import audit, latest_session_date


def trade(signal_id, entry_time, exit_time, ask, bid, cash_before, cash_after_entry, cash_after):
    gross = (bid - ask) * 100
    net = gross - 0.11
    return {
        "signal_id": signal_id,
        "hypothesis": "CALL_FLOW_REVERSAL_V01",
        "decision_date": "2026-10-07",
        "entry_time": entry_time,
        "signal_time": entry_time,
        "exit_time": exit_time,
        "status": "CLOSED",
        "quantity": 1,
        "entry_ask": ask,
        "exit_bid": bid,
        "capital_required": ask * 100,
        "cash_before": cash_before,
        "cash_after_entry": cash_after_entry,
        "gross_pnl": gross,
        "fees": 0.11,
        "net_pnl": net,
        "cash_after": cash_after,
        "exit_reason": "TP10",
        "selection": {
            "cash": cash_before,
            "risk_fraction": 0.40,
            "premium_budget": cash_before * 0.40,
        },
    }


def state_fixture():
    t1 = trade(
        "H01:A", "2026-10-07T13:30:00+00:00", "2026-10-07T13:40:00+00:00",
        3.00, 3.20, 1000.00, 700.00, 819.89,
    )
    t2 = trade(
        "H01:B", "2026-10-07T13:35:00+00:00", "2026-10-07T13:45:00+00:00",
        2.00, 2.10, 700.00, 500.00, 1029.78,
    )
    return {
        "epoch_id": "LIVE_TEST",
        "live_start_utc": "2026-10-07T00:00:00+00:00",
        "paper_risk_fraction": 0.40,
        "cash": 1029.78,
        "realized_net_pnl": 29.78,
        "pending_reconciliation_positions": 0,
        "live_ledger": [t1, t2],
    }


def test_audit_reconstructs_overlap_and_cash_timeline():
    result = audit(state_fixture(), "2026-10-07")
    s = result["summary"]

    assert result["status"] == "PASS_WITH_WARNINGS"
    assert s["trades"] == 2
    assert s["net_pnl"] == pytest.approx(29.78)
    assert s["daily_end_cash"] == pytest.approx(1029.78)
    assert s["max_concurrent_positions"] == 2
    assert s["max_cost_basis_exposure_fraction"] == pytest.approx(0.50)
    assert s["same_hypothesis_overlap_entries"] == 1
    assert s["same_hypothesis_overlap_pnl"] == pytest.approx(9.89)
    assert not result["diagnostics"]["event_cash_errors"]


def test_audit_fails_on_corrupted_trade_pnl():
    state = deepcopy(state_fixture())
    state["live_ledger"][0]["net_pnl"] += 5.0
    result = audit(state, "2026-10-07")

    assert result["status"] == "FAIL"
    assert result["diagnostics"]["pnl_errors"]


def test_latest_session_date_uses_latest_ledger_day():
    state = state_fixture()
    later = deepcopy(state["live_ledger"][0])
    later["decision_date"] = "2026-10-08"
    state["live_ledger"].append(later)

    assert latest_session_date(state) == "2026-10-08"
    assert latest_session_date({"live_ledger": []}) is None
