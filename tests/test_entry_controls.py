from datetime import datetime,timezone
from options_system.entry_controls import update_session_risk,entry_block

NOW=datetime(2026,10,7,15,tzinfo=timezone.utc)
SIGNAL={'hypothesis':'H01'}


def test_cooldown_uses_confirmed_past_exit_and_does_not_block_exit_path():
    ledger=[dict(hypothesis='H01',status='CLOSED',exit_time='2026-10-07T14:55:00Z',net_pnl=-10)]
    state={};update_session_risk(state,NOW,990,{},ledger)
    cfg=dict(cooldown_minutes=10,cooldown_hypotheses=['H01'])
    assert entry_block(SIGNAL,NOW,{},ledger,state,cfg)=='COOLDOWN_AFTER_EXIT'
    assert entry_block({'hypothesis':'H02'},NOW,{},ledger,state,cfg) is None
    ledger[0]['exit_time']='2026-10-07T15:01:00Z'
    assert entry_block(SIGNAL,NOW,{},ledger,state,cfg) is None


def test_one_position_counts_unresolved_positions_too():
    state={};positions={'x':dict(hypothesis='H01',quantity=1,last_bid=2,pending_reconciliation=True)}
    update_session_risk(state,NOW,800,positions,[])
    assert entry_block(SIGNAL,NOW,positions,[],state,{'max_positions_per_hypothesis':1})=='MAX_POSITIONS_PER_HYPOTHESIS'
    assert entry_block({'hypothesis':'H02'},NOW,positions,[],state,{'max_positions_per_hypothesis':1}) is None


def test_loss_halt_stays_latched_until_next_day_and_defaults_are_off():
    ledger=[dict(status='CLOSED',exit_time=f'2026-10-07T14:{m}:00Z',net_pnl=p) for m,p in [('20',-10),('30',-10),('40',5)]]
    state={};update_session_risk(state,NOW,985,{},ledger)
    assert entry_block(SIGNAL,NOW,{},ledger,state) is None
    assert entry_block(SIGNAL,NOW,{},ledger,state,{'max_consecutive_losses':2})=='CONSECUTIVE_LOSS_HALT'
    tomorrow=NOW.replace(day=8);update_session_risk(state,tomorrow,985,{},ledger)
    assert entry_block(SIGNAL,tomorrow,{},ledger,state,{'max_consecutive_losses':2}) is None


def test_daily_drawdown_marks_equity_before_new_entries():
    state={};update_session_risk(state,NOW,1000,{},[])
    positions={'x':dict(hypothesis='H01',quantity=1,last_bid=1.4)}
    update_session_risk(state,NOW,800,positions,[])
    assert round(state['max_drawdown_fraction'],4)==.06
    assert entry_block(SIGNAL,NOW,positions,[],state,{'max_daily_drawdown_fraction':.05})=='DAILY_DRAWDOWN_HALT'


def test_replay_reselects_contract_and_blocks_overlapping_hypothesis(monkeypatch):
    from options_system.prospective_paper_trader import replay_paper_account
    contract='SPY261009C00100000'
    def snapshot(ts,bid):
        return dict(captured_at_utc=ts,payload={'underlying':{'symbol':'SPY','snapshot':{'latestTrade':{'p':100,'t':ts}}},
                    'options':{'snapshot':{'snapshots':{contract:{'latestQuote':{'bp':bid,'ap':1.5,'bs':10,'as':10,'t':ts},
                                                               'dailyBar':{'v':100},'greeks':{'delta':.5}}}}}})
    ts='2026-10-07T14:00:00Z'
    signals=[dict(signal_id='one',hypothesis='H01',side='call',horizon_min=60,signal_time=ts,contract='old'),
             dict(signal_id='two',hypothesis='H01',side='call',horizon_min=60,signal_time='2026-10-07T14:01:00Z',contract='old')]
    result=replay_paper_account([snapshot(ts,1.45),snapshot('2026-10-07T14:01:00Z',1.45),
                                snapshot('2026-10-07T14:05:00Z',1.2)],signals,
                                {'status':'ACTIVE','allowed_max_fraction':.2},
                                policy={'entry_controls':{'max_positions_per_hypothesis':1}})
    closed=[r for r in result['ledger'] if r['status']=='CLOSED']
    blocked=[r for r in result['ledger'] if r['status']=='BLOCKED']
    assert len(closed)==1 and closed[0]['contract']==contract and closed[0]['frozen_tracker_contract']=='old'
    assert closed[0]['exit_reason']=='SL10' and blocked[0]['exit_reason']=='MAX_POSITIONS_PER_HYPOTHESIS'
    assert closed[0]['quantity']==1 and result['open_positions_count']==0


def test_replay_as_of_does_not_use_future_exit():
    from options_system.prospective_paper_trader import replay_paper_account
    contract='SPY261009C00100000';ts='2026-10-07T14:00:00Z'
    def snap(t,b):return {'captured_at_utc':t,'payload':{'options':{'snapshot':{'snapshots':{contract:{'latestQuote':{'bp':b,'t':t}}}}}}}
    signal=dict(signal_id='one',hypothesis='H01',side='call',horizon_min=60,signal_time=ts,
                contract=contract,entry_ask=1.5,entry_bid=1.45,entry_bid_size=10,entry_ask_size=10)
    result=replay_paper_account([snap(ts,1.45),snap('2026-10-07T14:05:00Z',1.8)],[signal],
                                {'status':'ACTIVE','allowed_max_fraction':.2},
                                policy={'select_executable_contract':False},
                                as_of=datetime(2026,10,7,14,1,tzinfo=timezone.utc))
    assert result['closed_trades']==0 and result['open_positions_count']==1
