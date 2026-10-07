import json
from datetime import datetime,timezone
import pytest
from options_system.paper_epochs import reset_epoch

NOW=datetime(2026,10,7,3,45,tzinfo=timezone.utc)


def fixture(root,positions=None):
    a=root/'artifacts/intraday';a.mkdir(parents=True)
    state=dict(mode='LIVE_PAPER',initial_cash=1000.,cash=703.8,equity=703.8,net_account_pnl=-296.2,
               realized_net_pnl=-296.2,closed_live_trades=20,reserved_capital=0.,open_positions=positions or [],
               live_ledger=[{'status':'CLOSED','net_pnl':-10}],seen_signal_ids=['old'],
               last_processed_snapshot_utc='2026-10-06T19:59:00Z')
    (a/'PAPER_TRADING_LIVE_STATE_V01.json').write_text(json.dumps(state))
    (a/'PAPER_TRADING_CONTROL_V01.json').write_text(json.dumps({'risk_fraction':.4}))
    (a/'FROZEN_HYPOTHESES_V02.json').write_text(json.dumps({'hypotheses':[],'frozen_at':'2026-10-02'}))
    (a/'PROSPECTIVE_RISK_GATE_V01.json').write_text(json.dumps({'allowed_max_fraction':.2}))
    csv=root/'data/processed/intraday/prospective_hypothesis_tracker_v02.csv';csv.parent.mkdir(parents=True)
    csv.write_text('captured_at_utc,decision_date,active_hypotheses\n')
    return a,state


def test_reset_archives_original_and_preserves_cursor_protection(tmp_path):
    a,old=fixture(tmp_path);control=(a/'PAPER_TRADING_CONTROL_V01.json').read_bytes()
    new=reset_epoch(tmp_path,'P1_20261007',as_of=NOW)
    assert new['cash']==new['equity']==1000. and new['net_account_pnl']==0
    assert new['live_ledger']==[] and new['closed_live_trades']==0
    assert new['seen_signal_ids']==['old'] and new['last_processed_snapshot_utc']==NOW.isoformat()
    assert new['paper_risk_fraction']==.4 and new['causal_replay_summary']=={}
    assert json.loads((tmp_path/new['previous_epoch_archive']/'state.json').read_text())==old
    assert (a/'PAPER_TRADING_CONTROL_V01.json').read_bytes()==control


def test_repeating_same_epoch_keeps_new_trades(tmp_path):
    a,_=fixture(tmp_path);new=reset_epoch(tmp_path,'P1_20261007',as_of=NOW)
    new['cash']=1020.;new['live_ledger']=[{'status':'CLOSED','net_pnl':20.}]
    (a/'PAPER_TRADING_LIVE_STATE_V01.json').write_text(json.dumps(new))
    repeated=reset_epoch(tmp_path,'P1_20261007',as_of=NOW)
    assert repeated['cash']==1020. and repeated['live_ledger']==new['live_ledger']


def test_open_position_rejects_reset_without_altering_state(tmp_path):
    a,old=fixture(tmp_path,[{'status':'INCOMPLETE'}])
    with pytest.raises(ValueError,match='open or unresolved'):
        reset_epoch(tmp_path,'P1_20261007',as_of=NOW)
    assert json.loads((a/'PAPER_TRADING_LIVE_STATE_V01.json').read_text())==old


def test_runner_does_not_replay_archived_signals_after_reset(tmp_path):
    import runpy,shutil
    from pathlib import Path
    a,_=fixture(tmp_path);reset_epoch(tmp_path,'P1_20261007',as_of=NOW)
    script=tmp_path/'scripts/run_live_paper_trader.py';script.parent.mkdir()
    shutil.copyfile(Path(__file__).resolve().parents[1]/'scripts/run_live_paper_trader.py',script)
    raw=tmp_path/'data/raw/prospective';raw.mkdir(parents=True)
    (raw/'spy_options_old.json').write_text(json.dumps({'captured_at_utc':'2026-10-06T19:59:00Z','payload':{}}))
    runpy.run_path(str(script))
    state=json.loads((a/'PAPER_TRADING_LIVE_STATE_V01.json').read_text())
    assert state['cash']==1000. and state['live_ledger']==[] and state['seen_signal_ids']==['old']
