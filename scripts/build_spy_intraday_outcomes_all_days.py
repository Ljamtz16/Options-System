import json,csv,os
from options_system.session_cache import snapshot_refs,fingerprint,write_csv,merge_csv,atomic_text,today
from pathlib import Path
from datetime import datetime,date,timedelta
from options_system.intraday_contracts import representative_contracts,conservative_long_pnl
from options_system.intraday_targets import option_trade_targets

ROOT=Path('data/raw/prospective');HORIZONS=(15,30,60)

def load_rows(day=None,refs=None):
    rows=[]
    day_filter=day
    for obj in (refs if refs is not None else snapshot_refs(ROOT,'spy_options_*.json')):
        if day_filter is not None and obj.day!=day_filter:continue
        p=obj['payload']
        rs=p.get('research_state') or {};day=(rs.get('features') or {}).get('decision_date')
        if not day: continue
        u=p['underlying']['snapshot'];t=u.get('latestTrade') or {};q=u.get('latestQuote') or {}
        spot=t.get('p') or (((q.get('bp') or 0)+(q.get('ap') or 0))/2 or None)
        if spot is None: continue
        rows.append({'day':day,'ts':datetime.fromisoformat(obj['captured_at_utc']),
                     'spot':float(spot),'chain':p['options']['snapshot']})
    return sorted(rows,key=lambda x:x['ts'])

def future(day_rows,i,minutes):
    target=day_rows[i]['ts']+timedelta(minutes=minutes)
    xs=[r for r in day_rows[i+1:] if target<=r['ts']<=target+timedelta(minutes=6)]
    return xs[0] if xs else None

def horizon_complete(day_rows,i,minutes):
    return future(day_rows,i,minutes) is not None

def contract_path(entry,day_rows,i,minutes):
    if not entry:return []
    end=day_rows[i]['ts']+timedelta(minutes=minutes)
    vals=[]
    for r in day_rows[i+1:]:
        if r['ts']>end+timedelta(minutes=6):break
        s=((r['chain'] or {}).get('snapshots') or {}).get(entry['symbol'])
        q=(s or {}).get('latestQuote') or {};bid=q.get('bp')
        if bid is not None and float(bid)>0:
            vals.append((r['ts'],float(bid)/float(entry['ask'])-1))
    return vals

def records_for_day(day,refs):
    rows=load_rows(day,refs);out=[]
    for day in sorted({r['day'] for r in rows}):
        dr=[r for r in rows if r['day']==day];md=date.fromisoformat(day)
        for i,r in enumerate(dr):
            reps=representative_contracts(r['chain'],md)
            rec={'decision_date':day,'captured_at_utc':r['ts'].isoformat(),'spot':r['spot']}
            for side in ('call','put'):
                e=reps.get(side)
                rec[f'{side}_contract']=e['symbol'] if e else None
                rec[f'{side}_entry_bid']=e['bid'] if e else None
                rec[f'{side}_entry_ask']=e['ask'] if e else None
                rec[f'{side}_entry_bid_size']=e.get('bid_size') if e else None
                rec[f'{side}_entry_ask_size']=e.get('ask_size') if e else None
            for h in HORIZONS:
                f=future(dr,i,h)
                if f:
                    rec[f'spy_ret_{h}m']=f['spot']/r['spot']-1
                    for side in ('call','put'):
                        pnl=conservative_long_pnl(reps.get(side),f['chain'])
                        rec[f'{side}_ret_{h}m']=pnl['return'] if pnl else None
                for side in ('call','put'):
                    path=[v for _,v in contract_path(reps.get(side),dr,i,h)]
                    # Path-based negative labels require full horizon coverage. A partial path
                    # can prove a first touch, but cannot prove that an untouched level would
                    # never have been reached before the requested horizon.
                    if path:
                        targets=option_trade_targets(path,f'{side}_{h}m')
                        touch=targets.get(f'{side}_{h}m_tp10_sl10')
                        if touch in ('TP_FIRST','SL_FIRST'):
                            threshold=.10 if touch=='TP_FIRST' else -.10
                            hit=next((v for v in path if v>=threshold),None) if touch=='TP_FIRST' else next((v for v in path if v<=threshold),None)
                            rec[f'{side}_{h}m_tp10_sl10_exit_return']=hit
                        if f or touch in ('TP_FIRST','SL_FIRST'):
                            rec.update(targets)
                        if f or max(path)>=.10:
                            rec[f'{side}_mfe_{h}m']=max(path)
                        if f:
                            rec[f'{side}_mae_{h}m']=min(path)
            out.append(rec)
    return out

def build():
    refs=snapshot_refs(ROOT,'spy_options_*.json')
    import hashlib
    algorithm=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    groups={}
    for ref in refs:groups.setdefault(ref.day,[]).append(ref)
    output=Path('data/processed/intraday/spy_intraday_outcomes_all_days.csv')
    directory=output.parent/'spy_sessions';manifest=directory/'manifest.json'
    try:known=json.loads(manifest.read_text())
    except (OSError,ValueError):known={}
    if output.exists() and not manifest.exists():
        seeded={}
        with output.open(newline='',encoding='utf-8') as f:
            reader=csv.DictReader(f);fields=reader.fieldnames
            for row in reader:seeded.setdefault(row['decision_date'],[]).append(row)
        for day,rows in seeded.items():
            write_csv(directory/(day+'.csv'),rows,fields)
            if len(rows)==len(groups.get(day,[])):known[day]=fingerprint(groups[day],algorithm)
    days=[today()] if os.getenv('OPTIONS_BUILD_SCOPE')=='today' else sorted(groups)
    for day in days:
        selected=groups.get(day,[])
        if not selected:continue
        digest=fingerprint(selected,algorithm)
        target=directory/(day+'.csv')
        if known.get(day)!=digest or not target.exists():
            write_csv(target,records_for_day(day,selected))
            known[day]=digest
            print('SPY_SESSION_BUILT',day,flush=True)
    atomic_text(manifest,json.dumps(known,sort_keys=True))
    count=merge_csv(directory,output)
    print(f'BUILT_SPY_INTRADAY_OUTCOMES rows={count}')

if __name__=='__main__':build()

