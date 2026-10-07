"""Causal long-option selection. A premium budget is not a stop-loss guarantee."""
import math
import re
from collections import Counter
from datetime import datetime, time
from decimal import Decimal
from zoneinfo import ZoneInfo

NY = ZoneInfo('America/New_York')
VERSION = 'executable_contract_v1'
DEFAULT_POLICY = dict(min_dte=1, max_dte=10, min_abs_delta=.25, max_abs_delta=.75,
                      target_abs_delta=.50, max_atm_distance=.01, max_spread_pct=.12,
                      min_volume=1, min_bid_size=1, min_ask_size=1,
                      quote_max_age_seconds=120, max_contract_price=5.)
OCC = re.compile(r'^([A-Z]+)(\d{6})([CP])(\d{8})$')


def number(value):
    try:
        n = float(value)
        return n if math.isfinite(n) else None
    except (TypeError, ValueError):
        return None


def stamp(value):
    out = value if isinstance(value, datetime) else datetime.fromisoformat(value.replace('Z', '+00:00'))
    if out.tzinfo is None:
        raise ValueError('Timezone required')
    return out


def contracts_from_snapshot(snapshot):
    """Read only the captured chain, never a provider or later snapshot."""
    captured = stamp(snapshot['captured_at_utc'])
    payload = snapshot['payload']
    stock = payload.get('underlying', {}).get('snapshot') or {}
    trade = stock.get('latestTrade') or {}
    spot = number(trade.get('p'))
    if trade.get('t') and stamp(trade['t']) > captured:
        spot = None
    if not spot:
        q = stock.get('latestQuote') or {}
        if not q.get('t') or stamp(q['t']) <= captured:
            bp, ap = number(q.get('bp')), number(q.get('ap'))
            if bp is not None and ap is not None and 0 < bp <= ap:
                spot = (bp + ap) / 2
    rows = []
    for symbol, item in payload.get('options', {}).get('snapshot', {}).get('snapshots', {}).items():
        q = item.get('latestQuote') or {}
        bar = item.get('dailyBar') or {}
        if bar.get('t') and stamp(bar['t']) > captured:
            bar = {}
        rows.append(dict(symbol=symbol, bid=q.get('bp'), ask=q.get('ap'), timestamp=q.get('t'),
                         bid_size=q.get('bs'), ask_size=q.get('as'), volume=bar.get('v'),
                         delta=(item.get('greeks') or {}).get('delta')))
    return rows, spot


def select_contract(contracts, side, timestamp, spot, cash, risk_fraction, quantity=1,
                    underlying='SPY', policy=None):
    cfg = dict(DEFAULT_POLICY, **(policy or {}))
    now = stamp(timestamp)
    day = now.astimezone(NY).date()
    start = datetime.combine(day, time(9, 30), NY)
    cash, fraction = number(cash), number(risk_fraction)
    spot = number(spot)
    if side.upper() not in ('CALL', 'PUT') or quantity < 1 or int(quantity) != quantity:
        raise ValueError('Invalid side or quantity')
    audit = dict(version=VERSION, policy=cfg, quantity=quantity, cash=cash,
                 risk_fraction=fraction, selected=None, eligible=0, rejected={}, status='BLOCKED')
    if cash is None or cash <= 0 or fraction is None or not 0 < fraction <= 1:
        return dict(audit, reason='INVALID_OR_ZERO_BUDGET')
    budget = min(Decimal(str(cash)), Decimal(str(cash)) * Decimal(str(fraction)))
    audit['premium_budget'] = float(budget)
    if spot is None or spot <= 0:
        return dict(audit, reason='MISSING_CAUSAL_SPOT')
    rejected, eligible = Counter(), []
    for row in contracts:
        reasons = []
        match = OCC.fullmatch(str(row.get('symbol', '')))
        if not match:
            rejected['INVALID_OCC'] += 1
            continue
        root, expiry, cp, strike = match.groups()
        try:
            expiry = datetime.strptime(expiry, '%y%m%d').date()
        except ValueError:
            rejected['INVALID_EXPIRY'] += 1
            continue
        dte, strike = (expiry - day).days, int(strike) / 1000.
        if root != underlying or cp != ('C' if side.upper() == 'CALL' else 'P'):
            continue
        if not cfg['min_dte'] <= dte <= cfg['max_dte']:
            reasons.append('DTE_OUT_OF_RANGE')
        bid, ask = number(row.get('bid')), number(row.get('ask'))
        if bid is None or ask is None or not 0 < bid <= ask:
            rejected['INVALID_QUOTE'] += 1
            continue
        spread = (ask - bid) / ask
        if spread > cfg['max_spread_pct']:
            reasons.append('SPREAD_ABOVE_LIMIT')
        if ask > cfg['max_contract_price']:
            reasons.append('PRICE_ABOVE_LIMIT')
        cost = Decimal(str(ask)) * 100 * int(quantity)
        if cost > budget:
            reasons.append('INSUFFICIENT_PREMIUM_BUDGET')
        try:
            qt = stamp(row['timestamp'])
            if qt < start or not 0 <= (now - qt).total_seconds() <= cfg['quote_max_age_seconds']:
                reasons.append('STALE_OR_FUTURE_QUOTE')
        except (KeyError, TypeError, ValueError, AttributeError):
            reasons.append('MISSING_QUOTE_TIME')
        for field, threshold in [('volume', cfg['min_volume']), ('bid_size', max(quantity, cfg['min_bid_size'])),
                                 ('ask_size', max(quantity, cfg['min_ask_size']))]:
            value = number(row.get(field))
            if value is None or value < threshold:
                reasons.append('LIQUIDITY_' + field.upper())
        distance = abs(strike / spot - 1.)
        delta = number(row.get('delta'))
        if delta is not None:
            if not cfg['min_abs_delta'] <= abs(delta) <= cfg['max_abs_delta'] or delta * (1 if cp == 'C' else -1) <= 0:
                reasons.append('DELTA_OUT_OF_RANGE')
            rank = abs(abs(delta) - cfg['target_abs_delta'])
            basis = 'DELTA'
        else:
            if distance > cfg['max_atm_distance']:
                reasons.append('ATM_DISTANCE_ABOVE_LIMIT')
            rank, basis = distance / max(cfg['max_atm_distance'], 1e-9), 'ATM_FALLBACK'
        if reasons:
            rejected.update(reasons)
            continue
        selected = dict(row, side=side.upper(), dte=dte, strike=strike, expiration=expiry.isoformat(),
                        delta=delta, atm_distance=distance, selection_basis=basis,
                        spread_pct=spread, premium_cost=float(cost))
        eligible.append(((rank, distance, spread, -number(row['volume']), dte, row['symbol']), selected))
    audit.update(eligible=len(eligible), rejected=dict(rejected))
    if not eligible:
        return dict(audit, reason='NO_EXECUTABLE_CONTRACT')
    audit.update(status='PASS', reason='SELECTED', selected=min(eligible, key=lambda x: x[0])[1])
    return audit


def select_signal(snapshot, signal, cash, fraction, policy=None):
    from .intraday_session import snapshot_close, close_time
    captured=stamp(snapshot['captured_at_utc'])
    local=captured.astimezone(NY)
    if local.time() < time(9,30) or captured >= close_time(snapshot['captured_at_utc'],snapshot_close(snapshot)):
        return dict(signal,frozen_tracker_contract=signal.get('contract'),contract=None,
                    entry_ask=None,entry_bid=None,entry_ask_size=None,entry_bid_size=None,
                    selection=dict(version=VERSION,status='BLOCKED',reason='OUTSIDE_SESSION',selected=None))
    rows, spot = contracts_from_snapshot(snapshot)
    audit = select_contract(rows, signal['side'], snapshot['captured_at_utc'], spot, cash, fraction,
                            underlying=snapshot['payload'].get('underlying', {}).get('symbol', 'SPY'), policy=policy)
    selected = audit['selected'] or {}
    return dict(signal, frozen_tracker_contract=signal.get('contract'), contract=selected.get('symbol'),
                entry_ask=selected.get('ask'), entry_bid=selected.get('bid'),
                entry_ask_size=selected.get('ask_size'), entry_bid_size=selected.get('bid_size'),
                entry_quote_time=selected.get('timestamp'), selection=audit)
