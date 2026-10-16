from __future__ import annotations
import csv,json,math
from dataclasses import dataclass
from datetime import datetime,timedelta,timezone
from pathlib import Path
from functools import lru_cache
from collections import Counter

ROOT=Path.home()/"options-system"
ART=ROOT/"artifacts/intraday"
RAW=ROOT/"data/raw/intraday"

def dt(v): return datetime.fromisoformat(str(v).replace('Z','+00:00'))
def num(v,default=None):
    try: return float(v)
    except (TypeError,ValueError): return default

@lru_cache(maxsize=4096)
def snap(name):
    p=RAW/name
    if not p.exists(): return None
    try: return json.loads(p.read_text())
    except Exception: return None

def quote(source_file,symbol,contract):
    d=snap(source_file)
    try:
        x=d['payload']['symbols'][symbol]['option_snapshot']['snapshots'][contract]
        q=x['latestQuote']; g=x.get('greeks') or {}
        return {'bid':num(q.get('bp')),'ask':num(q.get('ap')),'bid_size':num(q.get('bs')),'ask_size':num(q.get('as')),
                'quote_time':q.get('t'),'delta':num(g.get('delta'))}
    except Exception: return None

def load_authorizations(day):
    auth=[]
    for ln in (ART/'SIGNAL_EPISODE_LIVE_EVENTS_V01.jsonl').open():
        d=json.loads(ln)
        if d.get('would_authorize_new_trade') and str(d.get('episode_id','')).find(day)>=0:
            d=dict(d); d['_time']=dt(d['logged_at_utc']); auth.append(d)
    metas=[]
    for ln in (ART/'META_DECISION_LIVE_EVENTS_V01.jsonl').open():
        d=json.loads(ln)
        if d.get('day')==day: d=dict(d); d['_time']=dt(d.get('logged_at_utc') or d.get('time')); metas.append(d)
    by_ep={}
    for a in auth:
        choices=[m for m in metas if m.get('episode_id')==a.get('episode_id') and m['_time']<=a['_time']]
        m=max(choices,key=lambda x:x['_time']) if choices else None
        a['meta']=m
    return sorted(auth,key=lambda x:x['_time'])

def score(a):
    m=a.get('meta') or {}; src=a.get('source'); s=0.0
    if src=='H09': s+=40
    else: s+=20
    support=int(m.get('support_count') or 1)
    s += 20 if support==1 else -10
    if m.get('market_regime') in ('RISK_OFF','RISK_ON'): s+=20
    spread=num(m.get('spread_pct'),.12); s+=max(0,20*(1-min(spread/.12,1)))
    premium=(num(m.get('entry_ask'),0) or 0)*100; s+=max(0,10*(1-min(premium/1000,1)))
    s-=10*min(int(m.get('correlation_exposure') or 0),2)
    return round(s,4)

def load_rows(day):
    p=ROOT/f'data/processed/intraday/sessions/{day}.csv'
    rows=[]
    with p.open() as f:
        for r in csv.DictReader(f):
            r=dict(r); r['_time']=dt(r['captured_at_utc']); rows.append(r)
    by={}
    for r in rows: by.setdefault(r['symbol'],[]).append(r)
    return by

def at_or_after(rows,t,max_sec=95):
    cand=[r for r in rows if r['_time']>=t]
    if not cand: return None
    r=cand[0]
    return r if (r['_time']-t).total_seconds()<=max_sec else None

def executable(row,side,cash):
    pref='put' if side=='PUT' else 'call'; contract=row.get(f'entry_{pref}_contract'); ask=num(row.get(f'entry_{pref}_ask'))
    if not contract or not ask or ask<=0: return None
    q=quote(row['source_file'],row['symbol'],contract)
    if not q or not q['bid'] or not q['ask'] or q['bid']<=0 or q['ask']<=0: return None
    spread=(q['ask']-q['bid'])/q['ask']
    delta=abs(q['delta']) if q['delta'] is not None else None
    dte=num(row.get(f'entry_{pref}_dte'))
    reasons=[]
    if spread>.12: reasons.append('SPREAD')
    if delta is not None and not (.25<=delta<=.75): reasons.append('DELTA')
    if dte is not None and not (1<=dte<=10): reasons.append('DTE')
    if ask*100>cash: reasons.append('BUYING_POWER')
    if reasons: return {'ok':False,'reasons':reasons,'contract':contract,'ask':ask,'quote':q,'spread':spread}
    return {'ok':True,'reasons':[],'contract':contract,'ask':ask,'quote':q,'spread':spread,'delta':delta,'dte':dte}

def simulate(rows,entry_row,side,contract,entry_ask,horizon_min=30,tp=.10,sl=-.10):
    start=entry_row['_time']; end=start+timedelta(minutes=horizon_min); last=None; marks=0; mfe=-999; mae=999
    for r in rows:
        if r['_time']<start: continue
        if r['_time']>end: break
        q=quote(r['source_file'],r['symbol'],contract)
        if not q or not q['bid'] or q['bid']<=0: continue
        ret=q['bid']/entry_ask-1; marks+=1; mfe=max(mfe,ret); mae=min(mae,ret); last=(r,q,ret)
        if ret>=tp: return r['_time'],q['bid'],'TP10',ret,marks,mfe,mae
        if ret<=sl: return r['_time'],q['bid'],'SL10',ret,marks,mfe,mae
    if last:
        r,q,ret=last; return r['_time'],q['bid'],'HORIZON',ret,marks,mfe,mae
    return start,entry_ask,'NO_QUOTES',0.0,0,None,None

def replay(day,start_cash=1000.0,window_sec=90,daily_loss_halt_fraction=.10):
    auth=load_authorizations(day); by=load_rows(day); cash=start_cash; trades=[]; skipped=[]; i=0; available=datetime.min.replace(tzinfo=timezone.utc)
    halted=False
    while i<len(auth):
        if daily_loss_halt_fraction is not None and cash-start_cash <= -daily_loss_halt_fraction*start_cash:
            halted=True
            for rem in auth[i:]: skipped.append({'episode_id':rem['episode_id'],'reason':'DAILY_LOSS_HALT','time':rem['logged_at_utc']})
            break
        if auth[i]['_time']<available:
            skipped.append({'episode_id':auth[i]['episode_id'],'reason':'POSITION_OPEN','time':auth[i]['logged_at_utc']}); i+=1; continue
        t0=auth[i]['_time']; endw=t0+timedelta(seconds=window_sec); cluster=[]
        j=i
        while j<len(auth) and auth[j]['_time']<=endw:
            if auth[j]['_time']>=available: cluster.append(auth[j])
            j+=1
        ranked=sorted(cluster,key=score,reverse=True); entry_target=endw; chosen=None; ex=None; er=None
        for c in ranked:
            row=at_or_after(by[c['symbol']],entry_target)
            if not row:
                skipped.append({'episode_id':c['episode_id'],'reason':'NO_ENTRY_ROW','time':c['logged_at_utc']}); continue
            e=executable(row,c['side'],cash)
            if e and e['ok']:
                chosen,ex,er=c,e,row; break
            skipped.append({'episode_id':c['episode_id'],'reason':'NOT_EXECUTABLE:'+','.join((e or {}).get('reasons') or ['NO_CONTRACT']),'time':c['logged_at_utc']})
        if chosen:
            exit_t,exit_bid,reason,ret,marks,mfe,mae=simulate(by[chosen['symbol']],er,chosen['side'],ex['contract'],ex['ask'])
            gross=(exit_bid-ex['ask'])*100; fee=.11; net=gross-fee; before=cash; cash+=net
            trades.append({'episode_id':chosen['episode_id'],'source':chosen['source'],'symbol':chosen['symbol'],'side':chosen['side'],'score':score(chosen),
                           'cluster_size':len(cluster),'entry_time':er['captured_at_utc'],'contract':ex['contract'],'entry_ask':ex['ask'],'entry_spread_pct':ex['spread'],
                           'exit_time':exit_t.isoformat(),'exit_bid':exit_bid,'exit_reason':reason,'return':ret,'gross_pnl':gross,'fee':fee,'net_pnl':net,
                           'cash_before':before,'cash_after':cash,'mfe':mfe,'mae':mae,'marks':marks,'meta':{k:(chosen.get('meta') or {}).get(k) for k in ['strategy','candidate_ids','support_count','market_regime','correlation_exposure']}})
            available=exit_t
            for other in cluster:
                if other['episode_id']!=chosen['episode_id']:
                    skipped.append({'episode_id':other['episode_id'],'reason':'RANKED_OUT','time':other['logged_at_utc'],'score':score(other),'winner':chosen['episode_id']})
        i=j
    pnl=cash-start_cash; wins=sum(t['net_pnl']>0 for t in trades); losses=sum(t['net_pnl']<0 for t in trades)
    gp=sum(max(t['net_pnl'],0) for t in trades); gl=-sum(min(t['net_pnl'],0) for t in trades); peak=start_cash; maxdd=0.0
    for t in trades:
        peak=max(peak,t['cash_after']); maxdd=max(maxdd,(peak-t['cash_after'])/peak if peak else 0)
    by_source={}
    for src in sorted(set(t['source'] for t in trades)):
        z=[t for t in trades if t['source']==src]; by_source[src]={'trades':len(z),'net_pnl':sum(t['net_pnl'] for t in z),'wins':sum(t['net_pnl']>0 for t in z)}
    return {'version':'META_PORTFOLIO_REPLAY_V01','mode':'COUNTERFACTUAL_AFTER_CLOSE','day':day,'policy':{'start_cash':start_cash,'ranking_window_seconds':window_sec,'max_global_positions':1,'quantity':1,'tp_pct':.10,'sl_pct':-.10,'max_horizon_minutes':30,'daily_loss_halt_fraction':daily_loss_halt_fraction,'fixed_premium_cap':None,'buying_power_only':True},
            'summary':{'authorizations':len(auth),'trades':len(trades),'wins':wins,'losses':losses,'win_rate':wins/len(trades) if trades else None,'start_cash':start_cash,'end_cash':cash,'net_pnl':pnl,'return_fraction':pnl/start_cash,'tp':sum(t['exit_reason']=='TP10' for t in trades),'sl':sum(t['exit_reason']=='SL10' for t in trades),'horizon':sum(t['exit_reason']=='HORIZON' for t in trades),'profit_factor':gp/gl if gl else None,'max_drawdown_fraction':maxdd,'daily_halt_triggered':halted,'by_source':by_source},
            'trades':trades,'skipped':skipped,'warning':'Retrospective counterfactual. Ranking policy was specified before computing same-day P&L but was implemented after the session; not prospective evidence.'}

