import json,csv
from pathlib import Path
from datetime import datetime,date,timedelta
from options_system.intraday_contracts import representative_contracts,conservative_long_pnl
from options_system.intraday_targets import option_trade_targets

ROOT=Path('data/raw/prospective');HORIZONS=(15,30,60)

def load_rows():
    rows=[]
    for f in sorted(ROOT.glob('spy_options_*.json')):
        obj=json.loads(f.read_text(encoding='utf-8'));p=obj['payload']
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

def build():
    rows=load_rows();out=[]
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
    p=Path('data/processed/intraday/spy_intraday_outcomes_all_days.csv');p.parent.mkdir(parents=True,exist_ok=True)
    fields=sorted({k for r in out for k in r}) if out else []
    if fields:
        with open(p,'w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(out)
    print(f'BUILT_SPY_INTRADAY_OUTCOMES rows={len(out)}')

if __name__=='__main__':build()
