import json
from options_system.prospective_episode_tracker import build_episodes, build_virtual_account

H03={"id":"H03_CALL_RELATIVE_WEAKNESS_REVERSAL_V01","side":"call","horizon_min":60,
 "prospective_start_after":"2026-10-02",
 "episode_policy":{"gap_minutes":6,"entry":"first_activation_per_episode","max_contracts_per_episode":1,
 "entry_price":"ask","exit_price":"bid","tp":.10,"sl":-.10}}

def r(ts,date,contract,ask,outcome,exit_ret):
 return {"captured_at_utc":ts,"decision_date":date,"active_hypotheses":H03["id"],
 "call_contract":contract,"call_entry_ask":ask,"call_ret_60m":exit_ret,
 "call_mfe_60m":.14 if outcome=="TP_FIRST" else .04,
 "call_mae_60m":-.04 if outcome=="TP_FIRST" else -.12,
 "call_60m_tp10_sl10":outcome,"call_60m_tp10_sl10_exit_return":exit_ret}

def scenario():
 rows=[
  r("2026-10-02T16:30:00+00:00","2026-10-02","DISCOVERY",2.5,"TP_FIRST",.10),
  r("2026-10-05T14:00:00+00:00","2026-10-05","SPY_CALL_A",2.00,"TP_FIRST",.10),
  r("2026-10-05T14:05:00+00:00","2026-10-05","DUPLICATE",2.10,"TP_FIRST",.10),
  r("2026-10-05T15:00:00+00:00","2026-10-05","SPY_CALL_B",2.50,"SL_FIRST",-.10),
  r("2026-10-06T14:30:00+00:00","2026-10-06","SPY_CALL_C",3.00,"TP_FIRST",.10)]
 eps=build_episodes(rows,H03)
 return eps,build_virtual_account(eps,1000.0)

def test_dashboard_synthetic_scenario():
 eps,a=scenario()
 assert len(eps)==3
 assert eps[0]["activation_count"]==2 and eps[0]["contract"]=="SPY_CALL_A"
 assert [e["tp_sl"] for e in eps]==["TP_FIRST","SL_FIRST","TP_FIRST"]
 assert len({e["decision_date"] for e in eps})==2
 assert len(a["ledger"])==3
 assert a["final_cash"]>1000

if __name__=="__main__":
 eps,a=scenario()
 payload={"synthetic":True,"do_not_use_as_evidence":True,"prospective_episodes":eps,"virtual_account":a}
 print(json.dumps(payload,indent=2))
