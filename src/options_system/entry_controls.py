"""Optional entry controls; exits always run before these checks."""
from datetime import datetime
from zoneinfo import ZoneInfo

NY = ZoneInfo('America/New_York')
DEFAULT_CONTROLS = dict(cooldown_minutes=0, cooldown_hypotheses=[],
                        max_positions_per_hypothesis=0, max_consecutive_losses=0,
                        max_daily_drawdown_fraction=0.)


def stamp(s):
    return datetime.fromisoformat(s.replace('Z', '+00:00'))


def update_session_risk(state, now, cash, positions, ledger):
    day = now.astimezone(NY).date().isoformat()
    equity = cash + sum(float(p.get('last_bid') or 0) * 100 * int(p['quantity']) for p in positions.values())
    if state.get('day') != day:
        state.clear()
        state.update(day=day, peak_equity=equity, max_drawdown_fraction=0., halt_reasons=[])
    state['peak_equity'] = max(state['peak_equity'], equity)
    dd = max(0., (state['peak_equity'] - equity) / state['peak_equity']) if state['peak_equity'] > 0 else 0.
    state['max_drawdown_fraction'] = max(state['max_drawdown_fraction'], dd)
    state['equity'] = equity
    state['equity_is_estimate'] = any(p.get('pending_reconciliation') for p in positions.values())
    closed = [p for p in ledger if p.get('status') == 'CLOSED' and p.get('net_pnl') is not None
              and stamp(p['exit_time']).astimezone(NY).date().isoformat() == day
              and stamp(p['exit_time']) <= now]
    closed.sort(key=lambda p: stamp(p['exit_time']))
    current, maximum = 0, 0
    for p in closed:
        current = current + 1 if float(p['net_pnl']) < 0 else 0
        maximum = max(maximum, current)
    state.update(consecutive_losses=current, max_consecutive_losses=maximum)
    return state


def entry_block(signal, now, positions, ledger, state, policy=None):
    cfg = dict(DEFAULT_CONTROLS, **(policy or {}))
    maximum = int(cfg['max_positions_per_hypothesis'])
    if maximum and sum(p['hypothesis'] == signal['hypothesis'] for p in positions.values()) >= maximum:
        return 'MAX_POSITIONS_PER_HYPOTHESIS'
    if signal['hypothesis'] in cfg['cooldown_hypotheses'] and cfg['cooldown_minutes'] > 0:
        exits = [stamp(p['exit_time']) for p in ledger if p.get('status') == 'CLOSED'
                 and p.get('hypothesis') == signal['hypothesis'] and p.get('exit_time')
                 and stamp(p['exit_time']) <= now
                 and stamp(p['exit_time']).astimezone(NY).date() == now.astimezone(NY).date()]
        if exits and (now - max(exits)).total_seconds() < cfg['cooldown_minutes'] * 60:
            return 'COOLDOWN_AFTER_EXIT'
    if cfg['max_consecutive_losses'] and state['max_consecutive_losses'] >= cfg['max_consecutive_losses']:
        if 'CONSECUTIVE_LOSS_HALT' not in state['halt_reasons']:
            state['halt_reasons'].append('CONSECUTIVE_LOSS_HALT')
    if cfg['max_daily_drawdown_fraction'] and state['max_drawdown_fraction'] >= cfg['max_daily_drawdown_fraction']:
        if 'DAILY_DRAWDOWN_HALT' not in state['halt_reasons']:
            state['halt_reasons'].append('DAILY_DRAWDOWN_HALT')
    return state['halt_reasons'][0] if state['halt_reasons'] else None
