import math

EXCLUDE_PREFIX=('label_','call_ret_','put_ret_','spy_ret_','call_mfe_','put_mfe_','call_mae_','put_mae_')
EXCLUDE_EXACT={'captured_at_utc','decision_date','source_file','capture_id','active_hypotheses',
 'p_raw','p_calibrated','p_conservative','activity_pass','o6_decision','direction','decision','signal','prediction','score'}
EXCLUDE_MODEL_PREFIX=('p_','model_','pred_','prediction_','prob_','decision_','signal_')

def _f(x):
 try:
  v=float(x);return v if math.isfinite(v) else None
 except (TypeError,ValueError):return None

def quantile(xs,q):
 s=sorted(xs);i=(len(s)-1)*q;lo=int(i);hi=min(lo+1,len(s)-1);w=i-lo
 return s[lo]*(1-w)+s[hi]*w

def scan_univariate(rows,label,min_n=8):
 y=[r for r in rows if r.get(label) not in (None,'')]
 if not y:return []
 base=sum(int(r[label]) for r in y)/len(y);features=[]
 for k in y[0]:
  if k in EXCLUDE_EXACT or k.startswith(EXCLUDE_PREFIX) or k.startswith(EXCLUDE_MODEL_PREFIX):continue
  pairs=[(_f(r.get(k)),int(r[label])) for r in y];pairs=[p for p in pairs if p[0] is not None]
  vals=[p[0] for p in pairs]
  if len(vals)<min_n*2 or min(vals)==max(vals):continue
  for q in (.25,.5,.75):
   t=quantile(vals,q)
   for op in ('le','gt'):
    g=[yy for x,yy in pairs if (x<=t if op=='le' else x>t)]
    if len(g)<min_n:continue
    rate=sum(g)/len(g)
    features.append({'feature':k,'op':op,'threshold':t,'n':len(g),'rate':rate,
                     'baseline':base,'lift':rate/base if base else None})
 dedup={}
 for z in features:
  key=(z['feature'],z['op'],round(z['threshold'],12))
  dedup[key]=z
 return sorted(dedup.values(),key=lambda z:(z['lift'] or 0,z['n']),reverse=True)
