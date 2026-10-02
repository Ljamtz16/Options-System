import json,csv
from pathlib import Path
from datetime import datetime,date,timedelta
from options_system.intraday_contracts import representative_contracts,conservative_long_pnl

ROOT=Path('data/raw/prospective');HORIZONS=(15,30,60)

def load_rows():
    rows=[]
    for f in sorted(ROOT.glob('spy_options_*.json')):
        obj=json.loads(f.read_text(encoding='utf-8'));p=obj['payload']
        rs=p.get('research_state') or {};d=(rs.get('features') or {}).get('decision_date')
        if not d:continue
        u=p['underlying']['snapshot'];t=u.get('latestTrade') or {};q=u.get('latestQuote') or {}
        spot=t.get('p') or (((q.get('bp') or 0)+(q.get('ap') or 0))/2 or None)
        rows.append({'day':d,'ts':datetime.fromisoformat(obj['captured_at_utc']),'spot':float(spot),
                     'chain':p['options']['snapshot']})
    return sorted(rows,key=lambda x:x['ts'])

def future(day_rows,i,minutes):
    target=day_rows[i]['ts']+timedelta(minutes=minutes)
    xs=[r for r in day_rows[i+1:] if target<=r['ts']<=target+timedelta(minutes=6)]
    return xs[0] if xs else None

def build():
    rows=load_rows();out=[]
    for day in sorted({r['day'] for r in rows}):
        dr=[r for r in rows if r['day']==day];md=date.fromisoformat(day)
        for i,r in enumerate(dr):
            reps=representative_contracts(r['chain'],md)
            rec={'decision_date':day,'captured_at_utc':r['ts'].isoformat(),'spot':r['spot']}
            for h in HORIZONS:
                f=future(dr,i,h)
                if not f:continue
                rec[f'spy_ret_{h}m']=f['spot']/r['spot']-1
                for side in ('call','put'):
                    pnl=conservative_long_pnl(reps.get(side),f['chain'])
                    rec[f'{side}_ret_{h}m']=pnl['return'] if pnl else None
            out.append(rec)
    p=Path('data/processed/intraday/spy_intraday_outcomes_all_days.csv');p.parent.mkdir(parents=True,exist_ok=True)
    fields=sorted({k for r in out for k in r}) if out else []
    if fields:
        with open(p,'w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(out)
    print(f'BUILT_SPY_INTRADAY_OUTCOMES rows={len(out)}')

if __name__=='__main__':build()
