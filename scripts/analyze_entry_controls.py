"""Reproducible P2 scenarios. Never selects or activates a winning policy."""
import argparse
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from options_system.prospective_paper_trader import build_paper_signals, replay_paper_account

ROOT = Path(__file__).resolve().parents[1]
H01 = 'CALL_FLOW_REVERSAL_V01'
SCENARIOS = {
    'baseline': {},
    **{f'h01_cooldown_{m}m': dict(cooldown_minutes=m, cooldown_hypotheses=[H01]) for m in (5, 10, 15, 30)},
    'one_position_per_hypothesis': dict(max_positions_per_hypothesis=1),
    **{f'loss_streak_{n}': dict(max_consecutive_losses=n) for n in (2, 3, 4)},
    **{f'daily_dd_{int(100*d)}pct': dict(max_daily_drawdown_fraction=d) for d in (.02, .05, .10)},
    'combined_candidate': dict(cooldown_minutes=10, cooldown_hypotheses=[H01],
                               max_positions_per_hypothesis=1, max_consecutive_losses=3,
                               max_daily_drawdown_fraction=.05),
}


def run(root=ROOT, as_of=None):
    as_of = as_of or datetime.now(timezone.utc)
    a = root / 'artifacts/intraday'
    frozen = json.loads((a / 'FROZEN_HYPOTHESES_V02.json').read_text())
    risk = json.loads((a / 'PROSPECTIVE_RISK_GATE_V01.json').read_text())
    control_path = a / 'PAPER_TRADING_CONTROL_V01.json'
    control = json.loads(control_path.read_text()) if control_path.exists() else {}
    risk['allowed_max_fraction'] = float(control.get('risk_fraction', risk.get('allowed_max_fraction') or 0))
    risk['status'] = 'ACTIVE' if risk['allowed_max_fraction'] > 0 else 'BLOCKED'
    tracker = root / 'data/processed/intraday/prospective_hypothesis_tracker_v02.csv'
    with tracker.open() as f:
        signals = build_paper_signals(list(csv.DictReader(f)), frozen['hypotheses'], frozen['frozen_at'])
    signals=[s for s in signals if datetime.fromisoformat(s['signal_time'].replace('Z','+00:00'))<=as_of]
    snapshots, inputs = [], []
    for p in sorted((root / 'data/raw/prospective').glob('spy_options_*.json')):
        obj = json.loads(p.read_text())
        digest = hashlib.sha256(json.dumps(obj['payload'], sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()
        if digest != obj['sha256']:
            raise ValueError('Snapshot checksum mismatch: ' + p.name)
        if datetime.fromisoformat(obj['captured_at_utc'].replace('Z', '+00:00')) <= as_of:
            snapshots.append(obj)
            inputs.append(dict(file=p.name, sha256=digest))
    scenarios = {}
    for name, limits in SCENARIOS.items():
        result = replay_paper_account(snapshots, signals, risk, policy=dict(entry_controls=limits), as_of=as_of)
        days = {}
        for point in result['equity_curve']:
            day = point['day']
            prev = days.get(day, {})
            days[day] = dict(max_drawdown_fraction=max(prev.get('max_drawdown_fraction', 0), point['max_drawdown_fraction']),
                             max_consecutive_losses=max(prev.get('max_consecutive_losses', 0), point['max_consecutive_losses']),
                             ending_equity=point['equity'])
        scenarios[name] = {k: result[k] for k in ('cash', 'equity', 'equity_is_estimate', 'realized_net_pnl',
                        'closed_trades', 'blocked_signals', 'open_positions_count', 'pending_reconciliation_positions')}
        scenarios[name].update(controls=limits, daily=days,
            blocked_reasons=dict(Counter(p['exit_reason'] for p in result['ledger'] if p['status'] == 'BLOCKED')),
            ledger=[{k: p.get(k) for k in ('signal_id', 'hypothesis', 'signal_time', 'entry_time', 'entry_quote_time',
                 'contract', 'quantity', 'entry_ask', 'exit_time', 'exit_bid', 'exit_reason', 'status', 'net_pnl', 'fees')}
                 for p in result['ledger']])
    source_days = sorted({s['decision_date'] for s in signals})
    report = dict(version='entry_controls_analysis_v1', generated_at_utc=as_of.isoformat(),
                  mode='COUNTERFACTUAL_ANALYSIS', account_kind='LOCAL_SIMULATION',
                  scientific_evidence=False, auto_apply=False,
                  status='INSUFFICIENT_INDEPENDENT_DAYS' if len(source_days) < 20 else 'REVIEW_REQUIRED',
                  prospective_signal_days=source_days, minimum_days_for_review=20,
                  initial_cash=1000., premium_budget_fraction=risk['allowed_max_fraction'],
                  max_contracts_per_trade=1, cooldown_basis='AFTER_CONFIRMED_EXIT_SAME_NY_SESSION',
                  drawdown_basis='OBSERVED_MARK_TO_BID_EQUITY_FROM_SESSION_PEAK',
                  input_manifest_sha256=hashlib.sha256(json.dumps(inputs,sort_keys=True).encode()).hexdigest(),
                  scenarios=scenarios)
    target = a / 'ENTRY_CONTROLS_ANALYSIS_V01.json'
    tmp = target.with_suffix('.tmp'); tmp.write_text(json.dumps(report, indent=2, allow_nan=False)); tmp.replace(target)
    print(json.dumps(dict(status=report['status'], days=len(source_days),
                         scenarios={k:{x:v[x] for x in ('closed_trades','blocked_signals','realized_net_pnl')} for k,v in scenarios.items()})))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args(); run(args.root)
