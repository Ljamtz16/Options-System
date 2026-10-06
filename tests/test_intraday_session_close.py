from datetime import datetime,timezone
from options_system.intraday_session import finalize_positions,position_quote

def position(contract='SPY261009C00780000'):
 return dict(signal_id='test',contract=contract,status='OPEN',entry_time='2026-10-06T19:50:00Z',entry_ask=2.,quantity=1,capital_required=200.,last_bid=1.96,last_quote_time='2026-10-06T19:59:00Z')

def test_valid_same_day_close_and_cash_reconcile():
 positions={'test':position()};ledger=[]
 cash,net=finalize_positions(positions,ledger,800.,datetime(2026,10,6,20,1,tzinfo=timezone.utc))
 assert not positions and ledger[0]['exit_reason']=='SESSION_CLOSE'
 assert abs(cash-(1000.+net))<1e-8 and ledger[0]['exit_time']=='2026-10-06T19:59:00Z'

def test_missing_close_reserves_capital_unknown_pnl():
 pos=position();pos['last_quote_time']=None;positions={'test':pos};ledger=[]
 cash,net=finalize_positions(positions,ledger,800.,datetime(2026,10,6,20,1,tzinfo=timezone.utc))
 assert cash==800. and net==0. and positions['test']['status']=='INCOMPLETE'
 assert positions['test']['net_pnl'] is None and positions['test']['pending_reconciliation']
 cash,net=finalize_positions(positions,ledger,cash,datetime(2026,10,7,20,1,tzinfo=timezone.utc))
 assert cash==800. and not ledger

def test_expired_without_settlement_does_not_invent_zero():
 pos=position('SPY261006C00780000');pos['last_quote_time']=None
 positions={'test':pos};cash,net=finalize_positions(positions,[],800.,datetime(2026,10,6,20,1,tzinfo=timezone.utc))
 assert pos['status']=='EXPIRED' and pos['net_pnl'] is None and cash==800.

def test_next_day_quote_and_future_quote_rejected():
 pos=position();snapshot={'captured_at_utc':'2026-10-07T14:00:00Z'}
 assert position_quote(snapshot,pos,{'bid':3.,'quote_time':'2026-10-07T14:00:00Z'}) is None
 snapshot['captured_at_utc']='2026-10-06T19:55:00Z'
 assert position_quote(snapshot,pos,{'bid':3.,'quote_time':'2026-10-06T19:56:00Z'}) is None
 assert position_quote(snapshot,pos,{'bid':1.96,'quote_time':'2026-10-06T19:54:00Z'}) is not None

def test_early_close_uses_supplied_close():
 pos=position('SPY261130C00780000');pos.update(entry_time='2026-11-27T17:50:00Z',last_quote_time='2026-11-27T17:59:00Z',session_close_at_utc='2026-11-27T18:00:00Z')
 positions={'test':pos};ledger=[]
 finalize_positions(positions,ledger,800.,datetime(2026,11,27,18,1,tzinfo=timezone.utc))
 assert not positions and ledger[0]['exit_reason']=='SESSION_CLOSE'

def test_replay_closes_using_previous_session_bid_and_updates_totals(monkeypatch):
 import options_system.prospective_paper_trader as trader
 monkeypatch.setattr(trader,'evaluate_execution',lambda *a,**k:{'status':'PASS','max_contracts_by_risk_budget':1})
 contract='SPY261009C00780000'
 def snap(ts,bid):
  return {'captured_at_utc':ts,'payload':{'options':{'snapshot':{'snapshots':{contract:{'latestQuote':{'bp':bid,'ap':2.,'t':ts}}}}}}}
 ts='2026-10-06T19:50:00Z'
 signal=dict(signal_id='test',hypothesis='H01',decision_date='2026-10-06',signal_time=ts,horizon_min=60,contract=contract,entry_ask=2.,entry_bid=1.95,entry_ask_size=10,entry_bid_size=10)
 result=trader.replay_paper_account([snap(ts,1.95),snap('2026-10-06T19:59:00Z',1.96),snap('2026-10-07T14:00:00Z',3.)],[signal],{})
 assert result['closed_trades']==1 and result['open_positions_count']==0
 assert result['reserved_capital']==0. and result['ledger'][0]['exit_reason']=='SESSION_CLOSE'
 assert abs(result['cash']-result['equity'])<1e-8
 assert abs(result['cash']-(1000.+result['realized_net_pnl']))<1e-8
 assert result['ledger'][0]['exit_bid']==1.96

def test_live_runner_finalizes_without_new_capture(tmp_path):
 import csv,json,runpy,shutil
 from pathlib import Path
 root=tmp_path;script=root/'scripts/run_live_paper_trader.py';script.parent.mkdir()
 shutil.copyfile(Path(__file__).resolve().parents[1]/'scripts/run_live_paper_trader.py',script)
 a=root/'artifacts/intraday';a.mkdir(parents=True)
 (a/'FROZEN_HYPOTHESES_V02.json').write_text(json.dumps({'hypotheses':[],'frozen_at':'2026-10-02'}))
 (a/'PROSPECTIVE_RISK_GATE_V01.json').write_text(json.dumps({'allowed_max_fraction':.2}))
 pos=position();pos.update(entry_time='2026-10-05T19:50:00Z',last_quote_time='2026-10-05T19:59:00Z',signal_time='2026-10-05T19:50:00Z',last_mark_time='2026-10-05T19:59:00Z',mfe=0.,mae=0.,marks=1)
 state=dict(initial_cash=1000.,cash=800.,realized_net_pnl=0.,open_positions=[pos],live_ledger=[],seen_signal_ids=[],last_processed_snapshot_utc='2026-10-05T19:59:00Z')
 target=a/'PAPER_TRADING_LIVE_STATE_V01.json';target.write_text(json.dumps(state))
 runpy.run_path(str(script))
 saved=json.loads(target.read_text())
 assert not saved['open_positions'] and saved['closed_live_trades']==1
 assert saved['live_ledger'][0]['exit_reason']=='SESSION_CLOSE'
 assert abs(saved['cash']-(1000.+saved['realized_net_pnl']))<1e-8
