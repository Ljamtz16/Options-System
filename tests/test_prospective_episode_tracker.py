from options_system.prospective_episode_tracker import build_episodes,build_virtual_account

H03={"id":"H03_CALL_RELATIVE_WEAKNESS_REVERSAL_V01","side":"call","horizon_min":60,
     "prospective_start_after":"2026-10-02",
     "episode_policy":{"gap_minutes":6,"entry":"first_activation_per_episode","max_contracts_per_episode":1,
                       "entry_price":"ask","exit_price":"bid","tp":.10,"sl":-.10}}

def row(ts,date,contract,ask=2.0,exit_ret=.10):
    return {"captured_at_utc":ts,"decision_date":date,
            "active_hypotheses":H03["id"],"call_contract":contract,"call_entry_ask":ask,
            "call_ret_60m":exit_ret,"call_mfe_60m":.12,"call_mae_60m":-.04,
            "call_60m_tp10_sl10":"TP_FIRST","call_60m_tp10_sl10_exit_return":exit_ret}

def test_excludes_discovery_and_groups_first_activation():
    rows=[row("2026-10-02T16:30:00+00:00","2026-10-02","DISC"),
          row("2026-10-05T14:00:00+00:00","2026-10-05","A"),
          row("2026-10-05T14:05:00+00:00","2026-10-05","B"),
          row("2026-10-05T14:20:00+00:00","2026-10-05","C")]
    e=build_episodes(rows,H03)
    assert len(e)==2
    assert e[0]["contract"]=="A" and e[0]["activation_count"]==2
    assert e[1]["contract"]=="C"

def test_virtual_account_uses_one_contract_and_fees():
    e=build_episodes([row("2026-10-05T14:00:00+00:00","2026-10-05","A")],H03)
    a=build_virtual_account(e,1000)
    assert a["ledger"][0]["account_status"]=="EXECUTED"
    assert a["final_cash"]>1019 and a["final_cash"]<1021

def test_virtual_account_skips_contract_above_cash():
    e=build_episodes([row("2026-10-05T14:00:00+00:00","2026-10-05","A",ask=11)],H03)
    a=build_virtual_account(e,1000)
    assert a["ledger"][0]["account_status"]=="SKIP_INSUFFICIENT_CASH"
    assert a["final_cash"]==1000

def test_h03_frozen_contract_is_unchanged():
    import json
    from pathlib import Path
    p=Path(__file__).resolve().parents[1]/"artifacts/intraday/FROZEN_HYPOTHESES_V02.json"
    meta=json.loads(p.read_text(encoding="utf-8"))
    h=next(x for x in meta["hypotheses"] if x["id"]=="H03_CALL_RELATIVE_WEAKNESS_REVERSAL_V01")
    assert h["prospective_start_after"]=="2026-10-02"
    assert h["rules"]==[
        {"feature":"iwm_from_open","op":"<=","value":-0.003338055604745982},
        {"feature":"spy_from_open","op":"<=","value":-0.002140966419266088},
    ]
    assert h["episode_policy"]=={
        "gap_minutes":6,"entry":"first_activation_per_episode","max_contracts_per_episode":1,
        "entry_price":"ask","exit_price":"bid","tp":0.1,"sl":-0.1,
    }
