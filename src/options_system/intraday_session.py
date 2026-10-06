"""Causal close policy for local intraday accounts; unknown proceeds stay reserved."""
from datetime import datetime,time
from zoneinfo import ZoneInfo
from .option_costs import one_contract_trade,daily_regulatory_fees

NY=ZoneInfo('America/New_York')

def stamp(value):
    dt=datetime.fromisoformat(value.replace('Z','+00:00'))
    if dt.tzinfo is None:raise ValueError('Timezone missing')
    return dt


def close_time(entry_time, explicit=None):
    entry=stamp(entry_time);day=entry.astimezone(NY).date()
    close=stamp(explicit) if explicit else datetime.combine(day,time(16),NY)
    if close.astimezone(NY).date()!=day:raise ValueError('Invalid session close')
    return close


def position_quote(snapshot,position,quote):
    if not quote or not quote.get('quote_time'):return None
    now=stamp(snapshot['captured_at_utc']);qt=stamp(quote['quote_time'])
    entry=stamp(position.get('entry_time') or position['signal_time'])
    close=close_time(entry.isoformat(),position.get('session_close_at_utc'))
    if position.get('status') in ('EXPIRED','INCOMPLETE'):return None
    if not entry<qt<=min(now,close) or now>close:return None
    if (now-qt).total_seconds()>120:return None
    return quote


def finalize_positions(positions,ledger,cash,as_of):
    """Return cash and realized delta. No settlement or synthetic zero-P&L close."""
    now=stamp(as_of) if isinstance(as_of,str) else as_of
    realized=0.0
    for sid in list(positions):
        pos=positions[sid]
        entry_time=pos.get('entry_time') or pos['signal_time']
        close=close_time(entry_time,pos.get('session_close_at_utc'))
        if now<close or pos.get('status') in ('EXPIRED','INCOMPLETE'):continue
        mark=pos.get('last_quote_time')
        bid=pos.get('last_bid')
        if mark and bid is not None and stamp(entry_time)<stamp(mark)<=close and 0<=(close-stamp(mark)).total_seconds()<=120:
            qty=int(pos['quantity']);entry=float(pos['entry_ask']);bid=float(bid)
            trade=one_contract_trade(entry,bid/entry-1)
            fee=(float(daily_regulatory_fees([trade])['total']) if trade else 0.)*qty
            gross=(bid-entry)*100*qty;net=gross-fee
            cash+=bid*100*qty-fee;realized+=net
            pos.update(status='CLOSED',exit_reason='SESSION_CLOSE',exit_time=mark,exit_bid=bid,
                       gross_pnl=gross,fees=fee,net_pnl=net,cash_after=cash,simulation_version='intraday_session_v2')
            ledger.append(dict(pos));del positions[sid]
        else:
            suffix=pos['contract'][-15:-9]
            expired=False
            try:
                expiry=datetime.strptime(suffix,'%y%m%d').date()
                expired=expiry<=stamp(entry_time).astimezone(NY).date()
            except ValueError:pass
            pos.update(status='EXPIRED' if expired else 'INCOMPLETE',exit_reason='EXPIRY_NO_VALID_CLOSE_QUOTE' if expired else 'SESSION_CLOSE_NO_VALID_QUOTE',
                       net_pnl=None,gross_pnl=None,pending_reconciliation=True,simulation_version='intraday_session_v2')
            # Keep the debited entry capital reserved until a documented reconciliation.
    return cash,realized


def snapshot_close(snapshot):
    value=(snapshot.get('payload',{}).get('market_clock') or {}).get('next_close')
    if value and stamp(value).astimezone(NY).date()==stamp(snapshot['captured_at_utc']).astimezone(NY).date():return value
    return None
