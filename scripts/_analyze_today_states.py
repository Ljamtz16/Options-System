import csv, json, math, statistics as st
from pathlib import Path

boot=list(csv.DictReader(open('artifacts/intraday/SPY_2026-10-02_BOOTSTRAP.csv',encoding='utf-8')))
market=list(csv.DictReader(open('data/processed/prospective/prospective_market_state_v1.csv',encoding='utf-8')))
idx={r['captured_at_utc']:r for r in market}
rows=[]
for b in boot:
    r=dict(idx.get(b['captured_at_utc'],{})); r.update(b); rows.append(r)
print('ROWS',len(rows),'MATCHED',sum(bool(idx.get(b['captured_at_utc'])) for b in boot))

FEATURES=['atm_iv','put_call_iv_skew','put_call_volume_ratio_1pct','put_volume_share_1pct',
          'spy_from_open','qqq_from_open','iwm_from_open','qqq_minus_spy_from_open',
          'iwm_minus_spy_from_open','premarket_return','premarket_range','open5_return',
          'open5_range','d_atm_iv_prev','d_put_call_iv_skew_prev',
          'd_put_call_volume_ratio_1pct_prev']

def num(x):
    try:
        v=float(x); return v if math.isfinite(v) else None
    except:return None

def summarize(group):
    out={}
    for f in FEATURES:
        vals=[num(r.get(f)) for r in group]; vals=[v for v in vals if v is not None]
        if vals: out[f]={'n':len(vals),'mean':sum(vals)/len(vals),'median':st.median(vals)}
    return out

result={'rows':len(rows),'matched':sum(bool(idx.get(b['captured_at_utc'])) for b in boot),'horizons':{}}
for h in (15,30,60):
    result['horizons'][str(h)]={}
    for side in ('call','put'):
        key=f'{side}_ret_{h}m'; vals=[(num(r.get(key)),r) for r in rows]
        vals=[x for x in vals if x[0] is not None]; vals.sort(key=lambda x:x[0],reverse=True)
        n=len(vals); k=max(5,int(round(n*.20)))
        winners=[r for v,r in vals if v>=.10]; losers=[r for v,r in vals if v<=-.10]
        result['horizons'][str(h)][side]={'n':n,'top_n':k,
          'top':summarize([r for _,r in vals[:k]]),'bottom':summarize([r for _,r in vals[-k:]]),
          'gt10':summarize(winners),'ltm10':summarize(losers),
          'gt10_n':len(winners),'ltm10_n':len(losers),
          'top_windows':[{'ret':v,'ts':r['captured_at_utc'],'spot':num(r.get('spot'))} for v,r in vals[:5]]}
Path('artifacts/intraday/SPY_2026-10-02_STATE_ANALYSIS.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
