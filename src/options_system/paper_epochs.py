"""Archive and reset local LIVE_PAPER only; never contact a broker."""
import csv
import hashlib
import json
import math
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from .prospective_paper_trader import build_paper_signals
from .executable_contracts import DEFAULT_POLICY


def acquire_state_lock(state_path, timeout=30):
    path=Path(state_path).with_suffix('.lock');path.parent.mkdir(parents=True,exist_ok=True)
    handle=path.open('a+b');started=time.monotonic()
    if os.name=='nt':
        import msvcrt
        handle.seek(0);handle.write(b'0');handle.flush()
    while True:
        try:
            if os.name=='nt':
                handle.seek(0);msvcrt.locking(handle.fileno(),msvcrt.LK_NBLCK,1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
            return handle
        except (BlockingIOError,OSError):
            if time.monotonic()-started>=timeout:
                handle.close();raise TimeoutError('LIVE_PAPER state is busy')
            time.sleep(.1)


def reset_epoch(root, epoch_id, initial_cash=1000., as_of=None):
    root=Path(root);now=as_of or datetime.now(timezone.utc)
    if now.tzinfo is None or not math.isfinite(initial_cash) or initial_cash<=0:
        raise ValueError('Invalid start time or capital')
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,80}',epoch_id):
        raise ValueError('Invalid epoch id')
    a=root/'artifacts/intraday';path=a/'PAPER_TRADING_LIVE_STATE_V01.json'
    with acquire_state_lock(path):
        original=path.read_bytes();old=json.loads(original)
        if old.get('epoch_id')==epoch_id:
            return old
        if old.get('open_positions') or float(old.get('reserved_capital') or 0)>0:
            raise ValueError('Cannot reset LIVE_PAPER with open or unresolved positions')
        if old.get('mode') not in (None,'LIVE_PAPER'):
            raise ValueError('Only the local LIVE_PAPER account can be reset')
        control_path=a/'PAPER_TRADING_CONTROL_V01.json'
        control_raw=control_path.read_bytes();control=json.loads(control_raw)
        frozen=json.loads((a/'FROZEN_HYPOTHESES_V02.json').read_text())
        risk=json.loads((a/'PROSPECTIVE_RISK_GATE_V01.json').read_text())
        tracker=root/'data/processed/intraday/prospective_hypothesis_tracker_v02.csv'
        with tracker.open() as f:
            signals=build_paper_signals(list(csv.DictReader(f)),frozen['hypotheses'],frozen['frozen_at'])
        seen=set(old.get('seen_signal_ids') or [])
        seen.update(s['signal_id'] for s in signals if datetime.fromisoformat(s['signal_time'].replace('Z','+00:00'))<=now)
        archive=a/'paper_epochs'/('before_'+epoch_id)
        archive.mkdir(parents=True,exist_ok=False)
        (archive/'state.json').write_bytes(original)
        (archive/'control.json').write_bytes(control_raw)
        config=dict(premium_budget_fraction=float(control['risk_fraction']),max_contracts_per_trade=1,
                    entry_controls=control.get('entry_controls') or {},contract_selection_version='executable_contract_v1',
                    contract_selection_policy=dict(DEFAULT_POLICY),simulation_version='intraday_session_v2',tp=.10,sl=-.10)
        manifest=dict(archived_at_utc=now.isoformat(),old_epoch_id=old.get('epoch_id','LEGACY'),new_epoch_id=epoch_id,
                      prior_cash=old['cash'],prior_equity=old.get('equity'),prior_net_account_pnl=old.get('net_account_pnl'),
                      prior_closed_live_trades=old.get('closed_live_trades'),
                      state_sha256=hashlib.sha256(original).hexdigest(),control_sha256=hashlib.sha256(control_raw).hexdigest())
        (archive/'manifest.json').write_text(json.dumps(manifest,indent=2))
        state=dict(version='v0.2',mode='LIVE_PAPER',account_kind='LOCAL_SIMULATION',scientific_evidence=False,
                   purpose='prospective_execution_simulation_only',epoch_id=epoch_id,epoch_start_utc=now.isoformat(),
                   live_start_utc=now.isoformat(),initial_cash=initial_cash,cash=initial_cash,equity=initial_cash,
                   realized_net_pnl=0.,net_account_pnl=0.,unrealized_pnl=0.,reserved_capital=0.,
                   closed_live_trades=0,blocked_live_signals=0,open_positions=[],live_ledger=[],
                   pending_reconciliation_positions=0,equity_is_estimate=False,seen_signal_ids=sorted(seen),
                   last_processed_snapshot_utc=now.isoformat(),previous_snapshot_cursor=old.get('last_processed_snapshot_utc'),
                   updated_at_utc=now.isoformat(),paper_risk_fraction=config['premium_budget_fraction'],
                   scientific_risk_fraction=float(risk.get('allowed_max_fraction') or 0),
                   simulation_version=config['simulation_version'],contract_selection_version=config['contract_selection_version'],
                   session_risk={},entry_controls=config['entry_controls'],epoch_initial_configuration=config,
                   previous_epoch_archive=str(archive.relative_to(root)),previous_epoch_summary=manifest,
                   causal_replay_summary={},funding_source='NEW_VIRTUAL_CAPITAL_NO_REPLAY_CARRYOVER',
                   observation_plan=dict(technical_review_sessions=5,intermediate_review_sessions=10,
                                         primary_review_sessions=30,extended_review_sessions=[60,90],
                                         minimum_independent_trades_per_hypothesis=100,
                                         auto_apply_controls=False))
        tmp=path.with_suffix('.reset.tmp');tmp.write_text(json.dumps(state,indent=2,allow_nan=False));tmp.replace(path)
        return state
