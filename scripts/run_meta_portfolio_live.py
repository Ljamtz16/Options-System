#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,sys,time
from datetime import datetime,timezone,time as dtime
from pathlib import Path
from zoneinfo import ZoneInfo
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from options_system.meta_portfolio_live import init_state,latest_meta,enrich_auth,process_snapshot,atomic_json,append_event,close_position
ART=ROOT/'artifacts/intraday';RAW=ROOT/'data/raw/intraday'
STATE=ART/'META_PORTFOLIO_LIVE_STATE_V01.json'; EVENTS=ART/'META_PORTFOLIO_LIVE_EVENTS_V01.jsonl'; EP=ART/'SIGNAL_EPISODE_LIVE_EVENTS_V01.jsonl'; META=ART/'META_DECISION_LIVE_EVENTS_V01.jsonl'

def cycle():
 lines=EP.read_text().splitlines() if EP.exists() else []; files=sorted(RAW.glob('intraday_options_*.json'))
 if STATE.exists():state=json.loads(STATE.read_text())
 else:
  state=init_state(event_lines=len(lines),last_snapshot_file=files[-1].name if files else None);atomic_json(STATE,state);append_event(EVENTS,{'event':'META_PORTFOLIO_BASELINE','logged_at_utc':datetime.now(timezone.utc).isoformat(),'episode_event_line':len(lines),'last_snapshot_file':state['last_snapshot_file']});return state
 metas=latest_meta(META); offset=int(state.get('episode_event_line') or 0)
 for ln in lines[offset:]:
  try:d=json.loads(ln)
  except:continue
  if not d.get('would_authorize_new_trade'):continue
  ep=d.get('episode_id')
  if ep in set(state.get('seen_episode_ids') or []):continue
  state.setdefault('seen_episode_ids',[]).append(ep)
  x=enrich_auth(d,metas)
  if state.get('open_positions'):
   state.setdefault('skipped_authorizations',[]).append({'episode_id':ep,'time':d.get('logged_at_utc'),'reason':'POSITION_OPEN'})
   append_event(EVENTS,{'event':'META_PORTFOLIO_SKIP','logged_at_utc':datetime.now(timezone.utc).isoformat(),'episode_id':ep,'reason':'POSITION_OPEN'})
  else:state.setdefault('candidate_buffer',[]).append(x)
 state['episode_event_line']=len(lines)
 last=state.get('last_snapshot_file'); new=[p for p in files if last is None or p.name>last]
 for p in new:
  try:s=json.loads(p.read_text())
  except:continue
  process_snapshot(state,s,p.name,metas,EVENTS)
 # close at/after regular close if still open using last snapshot mark
 now=datetime.now(timezone.utc); ny_hour=now.astimezone(__import__('zoneinfo').ZoneInfo('America/New_York'))
 if state.get('open_positions') and (ny_hour.hour>16 or (ny_hour.hour==16 and ny_hour.minute>=0)):
  pos=state['open_positions'][0]
  close_position(state,pos,None,now,reason='SESSION_CLOSE',event_path=EVENTS)
 state['skipped_authorizations']=state.get('skipped_authorizations',[])[-500:];state['seen_episode_ids']=state.get('seen_episode_ids',[])[-2000:]
 state['updated_at_utc']=now.isoformat();atomic_json(STATE,state);return state

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--loop',action='store_true');ap.add_argument('--interval',type=float,default=5);a=ap.parse_args(); ny=ZoneInfo('America/New_York')
 while True:
  s=cycle();print('META_PORTFOLIO_LIVE',f"cash={s['cash']:.2f}",f"equity={s['equity']:.2f}",f"open={len(s['open_positions'])}",f"closed={len(s['live_ledger'])}",f"buffer={len(s['candidate_buffer'])}",flush=True)
  if not a.loop:return 0
  n=datetime.now(timezone.utc).astimezone(ny); t=n.time().replace(tzinfo=None); active=n.weekday()<5 and dtime(9,25)<=t<=dtime(16,5)
  time.sleep(a.interval if active else 60)
if __name__=='__main__':raise SystemExit(main())
