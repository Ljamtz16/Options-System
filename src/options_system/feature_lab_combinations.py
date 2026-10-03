from itertools import combinations
from .feature_lab_scan import scan_univariate,_f

ABSOLUTE_PRICE={'spot','spy_price','qqq_price','iwm_price','call_bid','call_ask','put_bid','put_ask'}

def applies(r,c):
 v=_f(r.get(c['feature']))
 return v is not None and (v<=c['threshold'] if c['op']=='le' else v>c['threshold'])

def temporal_stats(rows,label,conds):
 eligible=[r for r in rows if r.get(label) not in (None,'')]
 hit=[r for r in eligible if all(applies(r,c) for c in conds)]
 if not hit:return None
 hit=sorted(hit,key=lambda r:r.get('captured_at_utc',''))
 mid=len(eligible)//2
 first=set(id(x) for x in eligible[:mid])
 halves=[]
 for part in ([r for r in hit if id(r) in first],[r for r in hit if id(r) not in first]):
  halves.append({'n':len(part),'rate':sum(int(r[label]) for r in part)/len(part) if part else None})
 return hit,halves

def scan_combinations(rows,label,min_n=8,top_features=18,max_rules=3):
 uni=scan_univariate(rows,label,min_n)
 # Keep strongest threshold per feature; exclude absolute price levels from general candidates.
 pool=[];seen=set()
 for x in uni:
  if x['feature'] in ABSOLUTE_PRICE or x['feature'] in seen:continue
  seen.add(x['feature']);pool.append(x)
  if len(pool)>=top_features:break
 eligible=[r for r in rows if r.get(label) not in (None,'')]
 base=sum(int(r[label]) for r in eligible)/len(eligible)
 out=[]
 for size in range(2,max_rules+1):
  for conds in combinations(pool,size):
   ts=temporal_stats(rows,label,conds)
   if not ts:continue
   hit,halves=ts
   if len(hit)<min_n:continue
   rate=sum(int(r[label]) for r in hit)/len(hit)
   valid_halves=[h['rate'] for h in halves if h['n']>=3 and h['rate'] is not None]
   stable=len(valid_halves)==2 and min(valid_halves)>0
   out.append({'rules':[{'feature':c['feature'],'op':c['op'],'threshold':c['threshold']} for c in conds],
               'n':len(hit),'rate':rate,'baseline':base,'lift':rate/base if base else None,
               'first_half':halves[0],'second_half':halves[1],
               'temporal_support':stable,
               'min_half_rate':min(valid_halves) if len(valid_halves)==2 else None})
 return sorted(out,key=lambda z:(z['temporal_support'],z['min_half_rate'] or -1,z['lift'] or 0,z['n']),reverse=True)
