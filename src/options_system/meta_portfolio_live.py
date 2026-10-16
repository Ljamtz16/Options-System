from __future__ import annotations
import json,os,re
from datetime import datetime,timedelta,timezone,date
from pathlib import Path
from typing import Any
from options_system.meta_portfolio import dt,num,score

POLICY={
 'version':'META_PORTFOLIO_POLICY_V01','initial_cash':1000.0,'ranking_window_seconds':90,
 'max_global_positions':1,'quantity':1,'tp_pct':0.10,'sl_pct':-0.10,'max_horizon_minutes':30,
 'daily_loss_halt_fraction':0.10,'max_spread_pct':0.12,'min_abs_delta':0.25,'max_abs_delta':0.75,
 'min_dte':1,'max_dte':10,'fixed_premium_cap':None,'buying_power_only':True,
}
OCC_RE=re.compile(r'(\d{6})([CP])(\d{8})$')

def atomic_json(path:Path,data:dict):
 path.parent.mkdir(parents=True,exist_ok=True); tmp=path.with_suffix(path.suffix+'.tmp')
 tmp.write_text(json.dumps(data,indent=2,default=str)+'\n'); os.replace(tmp,path)

def append_event(path:Path,event:dict):
 path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('a') as f: f.write(json.dumps(event,sort_keys=True,default=str)+'\n')

def parse_contract(symbol:str,contract:str):
 m=OCC_RE.search(contract or '')
 if not m:return None
 try: exp=datetime.strptime(m.group(1),'%y%m%d').date()
 except ValueError:return None
 return {'expiration':exp,'side':'CALL' if m.group(2)=='C' else 'PUT'}

def symbol_options(snapshot:dict,symbol:str):
 try:return snapshot['payload']['symbols'][symbol]['option_snapshot']['snapshots']
 except Exception:return {}

def select_contract(snapshot:dict,symbol:str,side:str,cash:float,now:datetime,policy:dict|None=None):
 p={**POLICY,**(policy or {})}; best=[]
 for contract,x in symbol_options(snapshot,symbol).items():
  meta=parse_contract(symbol,contract)
  if not meta or meta['side']!=side: continue
  dte=(meta['expiration']-now.date()).days
  if not p['min_dte']<=dte<=p['max_dte']:continue
  q=x.get('latestQuote') or {}; g=x.get('greeks') or {}; bid=num(q.get('bp')); ask=num(q.get('ap')); delta=num(g.get('delta'))
  if not bid or not ask or bid<=0 or ask<=0 or delta is None:continue
  ad=abs(delta); spread=(ask-bid)/ask
  if not p['min_abs_delta']<=ad<=p['max_abs_delta']:continue
  if spread>p['max_spread_pct']:continue
  if num(q.get('bs'),0)<1 or num(q.get('as'),0)<1:continue
  if ask*100>cash:continue
  vol=num((x.get('dailyBar') or {}).get('v'),0)
  best.append((abs(ad-.5),spread,-vol,ask,contract,{'contract':contract,'bid':bid,'ask':ask,'bid_size':q.get('bs'),'ask_size':q.get('as'),'quote_time':q.get('t'),'delta':delta,'dte':dte,'spread_pct':spread,'volume':vol}))
 if not best:return None
 best.sort(key=lambda z:z[:4]); return best[0][-1]

def quote(snapshot:dict,symbol:str,contract:str):
 x=symbol_options(snapshot,symbol).get(contract) or {}; q=x.get('latestQuote') or {}
 bid=num(q.get('bp')); ask=num(q.get('ap'))
 if not bid or bid<=0:return None
 return {'bid':bid,'ask':ask,'quote_time':q.get('t')}

def init_state(now=None,event_lines=0,last_snapshot_file=None):
 now=now or datetime.now(timezone.utc); cash=POLICY['initial_cash']
 return {'version':'META_PORTFOLIO_LIVE_V01','mode':'LIVE_LOCAL_PAPER','account_kind':'META_LOCAL_SIMULATION','broker_orders_enabled':False,
  'live_start_utc':now.isoformat(),'policy':POLICY,'initial_cash':cash,'cash':cash,'equity':cash,'realized_net_pnl':0.0,
  'session_date':None,'daily_start_cash':cash,'open_positions':[],'live_ledger':[],'candidate_buffer':[],'skipped_authorizations':[],
  'seen_episode_ids':[],'episode_event_line':event_lines,'last_snapshot_file':last_snapshot_file,'updated_at_utc':now.isoformat()}

def latest_meta(meta_path:Path):
 out={}
 if not meta_path.exists():return out
 for ln in meta_path.open():
  try:d=json.loads(ln)
  except:continue
  ep=d.get('episode_id')
  if ep:out[ep]=d
 return out

def enrich_auth(d,metas):
 x=dict(d); x['meta']=metas.get(d.get('episode_id')); return x

def close_position(state,pos,snapshot,now,reason=None,event_path=None):
 q=quote(snapshot,pos['symbol'],pos['contract']) if snapshot else None
 if q:qbid=q['bid']; pos['last_bid']=qbid; pos['last_quote_time']=q.get('quote_time')
 else:qbid=num(pos.get('last_bid'))
 if not qbid:return False
 ret=qbid/pos['entry_ask']-1; why=reason
 if why is None:
  if ret>=POLICY['tp_pct']:why='TP10'
  elif ret<=POLICY['sl_pct']:why='SL10'
  elif (now-dt(pos['entry_time'])).total_seconds()>=POLICY['max_horizon_minutes']*60:why='HORIZON'
 if why is None:return False
 fee=.11; gross=(qbid-pos['entry_ask'])*100; net=gross-fee; state['cash']+=qbid*100-fee; state['realized_net_pnl']+=net
 pos.update(status='CLOSED',exit_time=now.isoformat(),exit_bid=qbid,exit_reason=why,gross_pnl=gross,fees=fee,net_pnl=net,cash_after=state['cash'])
 state['live_ledger'].append(dict(pos)); state['open_positions']=[]
 if event_path:append_event(event_path,{'event':'META_PORTFOLIO_EXIT','logged_at_utc':now.isoformat(),'signal_id':pos['signal_id'],'episode_id':pos['episode_id'],'symbol':pos['symbol'],'reason':why,'net_pnl':net})
 return True

def open_candidate(state,cand,snapshot,now,event_path=None):
 c=select_contract(snapshot,cand['symbol'],cand['side'],state['cash'],now)
 if not c:return False,'NO_EXECUTABLE_CONTRACT'
 capital=c['ask']*100; state['cash']-=capital
 sid='META:'+cand['episode_id']
 pos={'signal_id':sid,'episode_id':cand['episode_id'],'hypothesis':'META_PORTFOLIO_V01','source':cand['source'],'symbol':cand['symbol'],'side':cand['side'],
      'status':'OPEN','quantity':1,'contract':c['contract'],'entry_time':now.isoformat(),'signal_time':cand['logged_at_utc'],'entry_ask':c['ask'],'entry_bid':c['bid'],
      'entry_spread_pct':c['spread_pct'],'entry_delta':c['delta'],'entry_dte':c['dte'],'capital_required':capital,'cash_before':state['cash']+capital,'cash_after_entry':state['cash'],
      'score':score(cand),'market_regime':(cand.get('meta') or {}).get('market_regime'),'candidate_ids':(cand.get('meta') or {}).get('candidate_ids'),'support_count':(cand.get('meta') or {}).get('support_count'),
      'last_bid':c['bid'],'last_quote_time':c.get('quote_time'),'mfe':c['bid']/c['ask']-1,'mae':c['bid']/c['ask']-1,'marks':1}
 state['open_positions']=[pos]
 if event_path:append_event(event_path,{'event':'META_PORTFOLIO_ENTRY','logged_at_utc':now.isoformat(),'signal_id':sid,'episode_id':cand['episode_id'],'symbol':cand['symbol'],'source':cand['source'],'contract':c['contract'],'entry_ask':c['ask'],'score':score(cand),'broker_order':False})
 return True,None

def process_snapshot(state,snapshot,filename,metas,event_path=None):
 now=dt(snapshot.get('captured_at_utc')); day=now.date().isoformat()
 if state.get('session_date')!=day:
  state['session_date']=day; state['daily_start_cash']=state['cash']+sum(num(x.get('capital_required'),0) for x in state.get('open_positions') or [])
  state['candidate_buffer']=[]
 # mark open
 if state.get('open_positions'):
  pos=state['open_positions'][0]; q=quote(snapshot,pos['symbol'],pos['contract'])
  if q:
   ret=q['bid']/pos['entry_ask']-1; pos['last_bid']=q['bid'];pos['last_quote_time']=q.get('quote_time');pos['marks']=int(pos.get('marks') or 0)+1;pos['mfe']=max(num(pos.get('mfe'),ret),ret);pos['mae']=min(num(pos.get('mae'),ret),ret)
  close_position(state,pos,snapshot,now,event_path=event_path)
 # daily halt
 daily_pnl=(state['cash']-state['daily_start_cash']) if not state.get('open_positions') else None
 halted=daily_pnl is not None and daily_pnl<=-POLICY['daily_loss_halt_fraction']*state['daily_start_cash']
 # process ranking window if flat
 if not state.get('open_positions') and state.get('candidate_buffer') and not halted:
  buf=sorted(state['candidate_buffer'],key=lambda x:dt(x['logged_at_utc'])); first=buf[0]; end=dt(first['logged_at_utc'])+timedelta(seconds=POLICY['ranking_window_seconds'])
  if now>=end:
   cluster=[x for x in buf if dt(x['logged_at_utc'])<=end]; later=[x for x in buf if dt(x['logged_at_utc'])>end]
   ranked=sorted(cluster,key=score,reverse=True); winner=None
   for cand in ranked:
    if cand['symbol'] not in (snapshot.get('payload',{}).get('symbols') or {}):continue
    ok,reason=open_candidate(state,cand,snapshot,now,event_path)
    if ok:winner=cand;break
    state['skipped_authorizations'].append({'episode_id':cand['episode_id'],'time':cand['logged_at_utc'],'reason':reason})
   for cand in cluster:
    if winner and cand['episode_id']==winner['episode_id']:continue
    if not any(x.get('episode_id')==cand['episode_id'] for x in state['skipped_authorizations'][-len(cluster)-2:]):
     state['skipped_authorizations'].append({'episode_id':cand['episode_id'],'time':cand['logged_at_utc'],'reason':'RANKED_OUT','winner':winner['episode_id'] if winner else None})
   state['candidate_buffer']=later
 state['last_snapshot_file']=filename
 state['equity']=state['cash']+sum(num(x.get('last_bid'),x.get('entry_ask'))*100 for x in state.get('open_positions') or [])
 state['updated_at_utc']=now.isoformat();return state
