from options_system.prospective_episode_tracker import build_episodes,build_virtual_account

H03={"id":"H03_CALL_RELATIVE_WEAKNESS_REVERSAL_V01","side":"call","horizon_min":60,
 "prospective_start_after":"2026-10-02","episode_policy":{"gap_minutes":6,"entry":"first_activation_per_episode",
 "max_contracts_per_episode":1,"entry_price":"ask","exit_price":"bid","tp":.10,"sl":-.10}}
H01={"id":"CALL_FLOW_REVERSAL_V01","side":"call","horizon_min":60,"rules":{}}
H02={"id":"PUT_SKEW_SHORT_V01","side":"put","horizon_min":15,"rules":{}}

def row(ts,date,active,contract="C",ask=2.0,outcome="TP_FIRST",exit_ret=.10):
 return {"captured_at_utc":ts,"decision_date":date,"active_hypotheses":active,
 "call_contract":contract,"call_entry_ask":ask,"call_ret_60m":exit_ret,
 "call_mfe_60m":.12,"call_mae_60m":-.04,
 "call_60m_tp10_sl10":outcome,"call_60m_tp10_sl10_exit_return":exit_ret}

def test_no_h03_means_no_h03_episode():
 rows=[row("2026-10-05T14:00:00+00:00","2026-10-05",H01["id"])]
 assert build_episodes(rows,H03)==[]

def test_h01_h02_do_not_enter_h03_account():
 rows=[row("2026-10-05T14:00:00+00:00","2026-10-05",H01["id"]+";"+H02["id"]),
       row("2026-10-05T15:00:00+00:00","2026-10-05",H03["id"],contract="H03")]
 eps=build_episodes(rows,H03);a=build_virtual_account(eps,1000)
 assert len(eps)==1 and eps[0]["contract"]=="H03"
 assert len(a["ledger"])==1

def test_multiple_h03_episodes_same_day_are_independent():
 rows=[row("2026-10-05T14:00:00+00:00","2026-10-05",H03["id"],"A"),
       row("2026-10-05T14:05:00+00:00","2026-10-05",H03["id"],"DUP"),
       row("2026-10-05T14:20:00+00:00","2026-10-05",H03["id"],"B")]
 eps=build_episodes(rows,H03)
 assert len(eps)==2 and [e["contract"] for e in eps]==["A","B"]

def test_pending_outcome_does_not_change_cash():
 x=row("2026-10-05T14:00:00+00:00","2026-10-05",H03["id"])
 x["call_60m_tp10_sl10"]="PENDING";x["call_60m_tp10_sl10_exit_return"]=""
 eps=build_episodes([x],H03);a=build_virtual_account(eps,1000)
 assert a["ledger"][0]["account_status"]=="PENDING_OUTCOME"
 assert a["final_cash"]==1000

def test_contract_above_cash_is_skipped():
 eps=build_episodes([row("2026-10-05T14:00:00+00:00","2026-10-05",H03["id"],ask=10.01)],H03)
 a=build_virtual_account(eps,1000)
 assert a["ledger"][0]["account_status"]=="SKIP_INSUFFICIENT_CASH"
 assert a["final_cash"]==1000

def test_account_carries_forward_between_days():
 rows=[row("2026-10-05T14:00:00+00:00","2026-10-05",H03["id"],"A",2,.10 and "TP_FIRST",.10),
       row("2026-10-06T14:00:00+00:00","2026-10-06",H03["id"],"B",2,"SL_FIRST",-.10)]
 a=build_virtual_account(build_episodes(rows,H03),1000)
 day1=[x for x in a["ledger"] if x["decision_date"]=="2026-10-05"][0]
 day2=[x for x in a["ledger"] if x["decision_date"]=="2026-10-06"][0]
 assert day1["cash_after_day"]>1000
 assert day2["cash_before"]==day1["cash_after_day"]

def test_discovery_date_never_enters_account():
 eps=build_episodes([row("2026-10-02T14:00:00+00:00","2026-10-02",H03["id"])],H03)
 assert eps==[]
 assert build_virtual_account(eps,1000)["final_cash"]==1000


def test_same_day_trades_settle_sequentially():
 rows=[row("2026-10-05T14:00:00+00:00","2026-10-05",H03["id"],"A",2,"TP_FIRST",.10),
       row("2026-10-05T15:00:00+00:00","2026-10-05",H03["id"],"B",2,"SL_FIRST",-.10)]
 a=build_virtual_account(build_episodes(rows,H03),1000)
 first,second=a["ledger"]
 assert first["account_status"]=="EXECUTED" and second["account_status"]=="EXECUTED"
 assert second["cash_before_trade"]==first["cash_after_trade"]
 assert first["trade_net_pnl"]>0 and second["trade_net_pnl"]<0
 assert second["cash_after_trade"]==a["final_cash"]
