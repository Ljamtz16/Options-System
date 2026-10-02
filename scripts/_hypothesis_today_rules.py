import csv, math, json
boot=list(csv.DictReader(open('artifacts/intraday/SPY_2026-10-02_BOOTSTRAP.csv',encoding='utf-8')))
market=list(csv.DictReader(open('data/processed/prospective/prospective_market_state_v1.csv',encoding='utf-8')))
idx={r['captured_at_utc']:r for r in market}
rows=[]
for b in boot:
    r=dict(idx[b['captured_at_utc']]);r.update(b);rows.append(r)

def n(r,k):
    try:return float(r.get(k,''))
    except:return None

def evaluate(name, pred, side, h):
    ret=f'{side}_ret_{h}m'; chosen=[]
    for r in rows:
        v=n(r,ret)
        if v is None:continue
        try:ok=pred(r)
        except:ok=False
        if ok:chosen.append(v)
    if not chosen:return {'rule':name,'n':0}
    return {'rule':name,'n':len(chosen),'mean':sum(chosen)/len(chosen),
            'win_rate':sum(v>0 for v in chosen)/len(chosen),
            'gt10_rate':sum(v>=.10 for v in chosen)/len(chosen),
            'ltm10_rate':sum(v<=-.10 for v in chosen)/len(chosen)}

rules={
 'CALL_FLOW_REVERSAL':lambda r:(n(r,'d_atm_iv_prev') or 0)>0 and (n(r,'d_put_call_iv_skew_prev') or 0)<0 and (n(r,'d_put_call_volume_ratio_1pct_prev') or 0)>0,
 'CALL_WEAK_MARKET_FLOW_REVERSAL':lambda r:(n(r,'spy_from_open') is not None and n(r,'spy_from_open')<-.0015 and (n(r,'d_atm_iv_prev') or 0)>0 and (n(r,'d_put_call_iv_skew_prev') or 0)<0 and (n(r,'d_put_call_volume_ratio_1pct_prev') or 0)>0),
 'PUT_EARLY_WEAKNESS':lambda r:(n(r,'spy_from_open') is not None and -.0020<n(r,'spy_from_open')<0 and (n(r,'put_call_iv_skew') or 0)>.0045),
 'PUT_SKEW_HIGH_RATIO_LOW':lambda r:(n(r,'put_call_iv_skew') or 0)>.0045 and (n(r,'put_call_volume_ratio_1pct') or 9)<1.05,
}
out=[]
for h in (15,30,60):
 for side in ('call','put'):
  for name,p in rules.items():out.append({'h':h,'side':side,**evaluate(name,p,side,h)})
print(json.dumps(out,indent=2))
open('artifacts/intraday/SPY_2026-10-02_HYPOTHESIS_RULES.json','w').write(json.dumps(out,indent=2))
