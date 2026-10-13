from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from options_system.put_research_shadow import analyze, HYPOTHESES


def rows_for_downtrend():
    start = datetime(2026, 10, 13, 14, 0, tzinfo=timezone.utc)
    rows = []
    for i in range(40):
        rows.append({"decision_date": "2026-10-13", "captured_at_utc": (start + timedelta(minutes=i)).isoformat(),
                     "spot": str(800 - i * 0.3), "spy_from_open": "-0.002", "qqq_from_open": "-0.004",
                     "iwm_from_open": "-0.005", "put_contract": "SPY261016P00800000",
                     "put_entry_ask": "2.0", "put_entry_bid": "1.9", "put_entry_ask_size": "5",
                     "put_entry_bid_size": "4", "put_ret_15m": "0.2", "put_15m_tp10_sl10": "TP_FIRST"})
    return rows


def test_breakdown_and_continuation_produce_research_only_episodes():
    result = analyze(rows_for_downtrend())
    assert result["mode"] == "RESEARCH_ONLY_NO_ORDERS"
    assert result["summary"]["H06_PUT_BREAKDOWN"]["episodes"] >= 1
    assert result["summary"]["H08_PUT_CONTINUATION"]["episodes"] >= 1


def test_no_future_data_leakage_into_earlier_decisions():
    rows = rows_for_downtrend()
    base = analyze(rows[:30])
    changed = rows_for_downtrend()
    for row in changed[30:]:
        row["spot"] = "900"
        row["put_ret_15m"] = "-0.9"
    changed_result = analyze(changed)
    earlier = lambda report: [(e["hypothesis"], e["captured_at_utc"]) for e in report["episodes"] if e["captured_at_utc"] < rows[30]["captured_at_utc"]]
    assert earlier(base) == earlier(changed_result)


def test_outcomes_never_change_signal_decisions():
    rows = rows_for_downtrend()
    base = analyze(rows)
    for row in rows:
        row["put_ret_15m"] = "-0.5"
        row["put_15m_tp10_sl10"] = "SL_FIRST"
    altered = analyze(rows)
    assert [(e["hypothesis"], e["captured_at_utc"]) for e in base["episodes"]] == [(e["hypothesis"], e["captured_at_utc"]) for e in altered["episodes"]]


def test_missing_quote_blocks_every_strategy():
    rows = rows_for_downtrend()
    for row in rows:
        row["put_entry_ask"] = ""
    report = analyze(rows)
    assert all(report["summary"][h]["episodes"] == 0 for h in HYPOTHESES)


def test_daily_history_reset():
    rows = rows_for_downtrend()
    rows2 = [dict(r, decision_date="2026-10-14", captured_at_utc=r["captured_at_utc"].replace("2026-10-13", "2026-10-14")) for r in rows]
    report = analyze(rows + rows2)
    assert report["summary"]["H06_PUT_BREAKDOWN"]["days_with_episodes"] == 2


def test_failed_rebound_requires_trough_before_bounce():
    rows = rows_for_downtrend()
    start = datetime(2026, 10, 13, 14, 0, tzinfo=timezone.utc)
    rows = []
    for i in range(55):
        if i < 30:
            price = 800 - i * .23
        elif i < 36:
            price = 800 - 29 * .23 + (i - 29) * .24
        else:
            price = 800 - 29 * .23 + 6 * .24 - (i - 35) * .39
        rows.append({"decision_date": "2026-10-13", "captured_at_utc": (start + timedelta(minutes=i)).isoformat(),
                     "spot": str(price), "spy_from_open": "-0.003", "qqq_from_open": "-0.004",
                     "iwm_from_open": "-0.005", "put_contract": "SPY261016P00800000",
                     "put_entry_ask": "2.0", "put_entry_bid": "1.9", "put_ret_15m": "0.1"})
    report = analyze(rows)
    assert report["summary"]["H07_PUT_FAILED_REBOUND"]["episodes"] >= 1


def test_cross_market_missing_prevents_activation():
    rows = rows_for_downtrend()
    for row in rows:
        row["qqq_from_open"] = ""
    result = analyze(rows)
    assert all(result["summary"][h]["episodes"] == 0 for h in HYPOTHESES)

def test_wide_spread_prevents_activation():
    rows = rows_for_downtrend()
    for row in rows:
        row["put_entry_bid"] = "1.0"
    result = analyze(rows)
    assert all(result["summary"][h]["episodes"] == 0 for h in HYPOTHESES)

def test_duplicate_activation_groups_into_one_episode():
    rows = rows_for_downtrend()
    result = analyze(rows)
    assert result["summary"]["H06_PUT_BREAKDOWN"]["activations"] > result["summary"]["H06_PUT_BREAKDOWN"]["episodes"]
