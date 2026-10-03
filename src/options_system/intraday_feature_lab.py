import csv,json
from pathlib import Path
from datetime import datetime,date,time
from zoneinfo import ZoneInfo
from options_system.intraday_contracts import representative_contracts

def _f(x):
    try:return float(x)
    except (TypeError,ValueError):return None

def _b(x): return 1 if x else 0

def build_feature_lab(state_rows,outcome_rows,raw_dir):
    out_by_ts={r['captured_at_utc']:r for r in outcome_rows}
    chain_by_ts={}
    for p in sorted(Path(raw_dir).glob('spy_options_*.json')):
        o=json.loads(p.read_text(encoding='utf-8'));chain_by_ts[o['captured_at_utc']]=o['payload']['options']['snapshot']
    rows=[]
    for s in state_rows:
        x=dict(s);o=out_by_ts.get(s['captured_at_utc'],{});x.update(o)
        ts=datetime.fromisoformat(s['captured_at_utc']);x['utc_hour']=ts.hour;x['utc_minute']=ts.minute
        ny=ZoneInfo('America/New_York');utc=ZoneInfo('UTC')
        local_day=ts.astimezone(ny).date()
        first=datetime.combine(local_day,time(9,30),tzinfo=ny).astimezone(utc)
        x['minutes_from_us_open']=(ts.astimezone(utc)-first).total_seconds()/60
        reps=representative_contracts(chain_by_ts.get(s['captured_at_utc'],{}),date.fromisoformat(s['decision_date']))
        for side in ('call','put'):
            r=reps.get(side) or {};bid=_f(r.get('bid'));ask=_f(r.get('ask'))
            x[f'{side}_delta']=r.get('delta');x[f'{side}_dte']=r.get('dte')
            x[f'{side}_bid']=bid;x[f'{side}_ask']=ask
            x[f'{side}_spread_abs']=(ask-bid) if ask is not None and bid is not None else None
            x[f'{side}_spread_pct']=((ask-bid)/ask) if ask and bid is not None else None
            x[f'{side}_bid_size']=r.get('bid_size');x[f'{side}_ask_size']=r.get('ask_size');x[f'{side}_iv']=r.get('iv')
        for side in ('call','put'):
            for h in (15,30,60):
                mfe=_f(x.get(f'{side}_mfe_{h}m'));touch=x.get(f'{side}_{h}m_tp10_sl10')
                x[f'label_{side}_mfe10_{h}m']=None if mfe is None else _b(mfe>=.10)
                x[f'label_{side}_tp10_before_sl10_{h}m']=None if not touch else _b(touch=='TP_FIRST')
        rows.append(x)
    return rows

def write_csv(rows,path):
    if not rows:return 0
    fields=[]
    for r in rows:
        for k in r:
            if k not in fields:fields.append(k)
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    with open(path,'w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    return len(rows)
