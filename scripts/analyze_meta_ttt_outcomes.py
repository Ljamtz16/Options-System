#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,json
from collections import Counter,defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
ROOT=Path(__file__).resolve().parents[1]; ART=ROOT/'artifacts/intraday'
def dt(v): return datetime.fromisoformat(str(v).replace('Z','+00:00'))
def num(v):
 try:return float(v)
 except:return None

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--date'); a=ap.parse_args()
 if not a.date:
  dates=sorted(x.stem for x in (ROOT/'data/processed/intraday/sessions').glob('20*.csv'))
  a.date=dates[-1] if dates else None
 if not a.date: raise SystemExit('No session date available')
 rows=[]
 with (ROOT/f'data/processed/intraday/sessions/{a.date}.csv').open() as f:
  for r in csv.DictReader(f): r=dict(r); r['_time']=dt(r['captured_at_utc']); rows.append(r)
 by=defaultdict(list)
 for r in rows: by[r['symbol']].append(r)
 auth=[]
 for ln in (ART/'SIGNAL_EPISODE_LIVE_EVENTS_V01.jsonl').open():
  d=json.loads(ln)
  if d.get('would_authorize_new_trade') and a.date in str(d.get('episode_id')):
   d=dict(d); d['_time']=dt(d['logged_at_utc']); auth.append(d)
 out=[]
 for x in auth:
  candidates=by[x['symbol']]
  if not candidates: continue
  r=min(candidates,key=lambda z:abs((z['_time']-x['_time']).total_seconds()))
  if abs((r['_time']-x['_time']).total_seconds())>95: continue
  side='put' if x['side']=='PUT' else 'call'
  y={'episode_id':x['episode_id'],'source':x['source'],'symbol':x['symbol'],'side':x['side'],'authorization_time':x['logged_at_utc'],'outcome_row_time':r['captured_at_utc']}
  for h in (15,30,60):
   y[f'return_{h}m']=num(r.get(f'{side}_terminal_return_{h}m'))
   y[f'tp10_sl10_{h}m']=r.get(f'{side}_{h}m_tp10_sl10')
   y[f'mfe_{h}m']=num(r.get(f'{side}_best_return_{h}m'))
   y[f'mae_{h}m']=num(r.get(f'{side}_worst_return_{h}m'))
  out.append(y)
 summary={}
 for src in ['ALL']+sorted(set(x['source'] for x in out)):
  z=out if src=='ALL' else [x for x in out if x['source']==src]
  d={'n':len(z)}
  for h in (15,30,60):
   vals=[x[f'return_{h}m'] for x in z if x[f'return_{h}m'] is not None]
   labs=Counter(x[f'tp10_sl10_{h}m'] for x in z if x.get(f'tp10_sl10_{h}m'))
   d[f'{h}m']={'n':len(vals),'mean_return':mean(vals) if vals else None,'positive_rate':sum(v>0 for v in vals)/len(vals) if vals else None,'tp_first':labs.get('TP_FIRST',0),'sl_first':labs.get('SL_FIRST',0),'neither':labs.get('NEITHER',0)}
  summary[src]=d
 result={'version':'META_TTT_OUTCOME_EVALUATOR_V01','mode':'POST_CLOSE_EVALUATION','date':a.date,'summary':summary,'rows':out}
 p=ART/'META_TTT_OUTCOMES_V01.json'; p.write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(summary,indent=2)); print('OUTPUT',p.resolve())
 return 0
if __name__=='__main__': raise SystemExit(main())
