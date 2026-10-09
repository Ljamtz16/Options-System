#!/usr/bin/env python3
import csv,json,statistics,hashlib
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];A=ROOT/'artifacts/intraday'

def load(path,default):
 try:return json.loads(path.read_text())
 except (OSError,ValueError):return default

def day_of(row):
 for key in ('decision_date','session_date'):
  if row.get(key):return str(row[key])[:10]
 for key in ('entry_time','signal_time','local_entry_time'):
  if row.get(key):return str(row[key])[:10]
 sid=str(row.get('signal_id') or '')
 for part in sid.split(':'):
  if len(part)==10 and part[4]=='-' and part[7]=='-':return part
 return 'UNKNOWN'

def max_dd(pnls,start=1000.0):
 eq=peak=start;dd=0.0
 for p in pnls:
  eq+=p;peak=max(peak,eq);dd=max(dd,(peak-eq)/peak if peak else 0)
 return dd

def freeze_status():
 cfg=load(ROOT/'config/observation_freeze_v01.json',{})
 drift=[]
 for rel,expected in cfg.get('sha256',{}).items():
  p=ROOT/rel;actual=hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
  if actual!=expected:drift.append(dict(file=rel,expected=expected,actual=actual))
 return dict(status='PASS' if not drift else 'DRIFT',drift=drift,config=cfg)

local=load(A/'PAPER_TRADING_LIVE_STATE_V01.json',{})
mirror=load(A/'OPTIONS_ALPACA_PAPER_STATE_V01.json',{})
from options_system.prospective_paper_trader import build_paper_signals
frozen=load(A/'FROZEN_HYPOTHESES_V02.json',{})
tracker=ROOT/'data/processed/intraday/prospective_hypothesis_tracker_v02.csv'
tracker_rows=list(csv.DictReader(tracker.open())) if tracker.exists() else []
activations=build_paper_signals(tracker_rows,frozen.get('hypotheses',{}),frozen.get('frozen_at','9999-12-31')) if frozen else []
controls=load(A/'ENTRY_CONTROLS_ANALYSIS_V01.json',{})
ledger=[r for r in local.get('live_ledger',[]) if r.get('status') in ('OPEN','CLOSED','BLOCKED')]
local_entered_all=[r for r in ledger if r.get('status')=='CLOSED']+[r for r in local.get('open_positions',[]) if r.get('status')=='OPEN']
mirror_start=mirror.get('mirror_start_utc')
def in_mirror_window(r):
 if not mirror_start:return True
 stamp=r.get('entry_time') or r.get('signal_time')
 if not stamp:return False
 return datetime.fromisoformat(str(stamp).replace('Z','+00:00')) >= datetime.fromisoformat(str(mirror_start).replace('Z','+00:00'))
local_entered=[r for r in local_entered_all if in_mirror_window(r)]
activations_window=[r for r in activations if in_mirror_window(r)]
trades=list((mirror.get('trades') or {}).values())
entry_filled=[r for r in trades if (r.get('entry_order') or {}).get('status')=='filled']
closed=[r for r in trades if r.get('status')=='CLOSED_FILLED']
local_pnls=[float(r.get('net_pnl') or 0) for r in ledger if r.get('status')=='CLOSED' and r.get('net_pnl') is not None]
broker_pnls=[float(r.get('broker_gross_pnl') or 0) for r in closed]
entry_slip=[float(r['entry_slippage_vs_local_ask']) for r in closed if r.get('entry_slippage_vs_local_ask') is not None]
exit_slip=[float(r['exit_slippage_vs_local_bid']) for r in closed if r.get('exit_slippage_vs_local_bid') is not None]
byday=defaultdict(lambda:dict(local=0,broker_entries=0,broker_closed=0,local_pnl=0.0,broker_pnl=0.0))
for r in local_entered_all:
 d=day_of(r);byday[d]['local']+=1;byday[d]['local_pnl']+=float(r.get('net_pnl') or 0)
for r in entry_filled:byday[day_of(r)]['broker_entries']+=1
for r in closed:
 d=day_of(r);byday[d]['broker_closed']+=1;byday[d]['broker_pnl']+=float(r.get('broker_gross_pnl') or 0)
base=(controls.get('scenarios') or {}).get('baseline',{})
filter_value={}
for name,row in (controls.get('scenarios') or {}).items():
 filter_value[name]=dict(blocked_signals=row.get('blocked_signals'),closed_trades=row.get('closed_trades'),realized_net_pnl=row.get('realized_net_pnl'),delta_vs_baseline=(None if row.get('realized_net_pnl') is None or base.get('realized_net_pnl') is None else row['realized_net_pnl']-base['realized_net_pnl']),blocked_reasons=row.get('blocked_reasons',{}))
session_pnls=[v['local_pnl'] for k,v in sorted(byday.items()) if k!='UNKNOWN']
report=dict(version='execution_funnel_v01',generated_at_utc=datetime.now(timezone.utc).isoformat(),freeze=freeze_status(),funnel=dict(mirror_start_utc=mirror_start,activations_in_mirror_window=len(activations_window),activations_by_hypothesis=dict(Counter(r.get('hypothesis','UNKNOWN') for r in activations_window)),local_selected_entered=len(local_entered),local_entered_epoch=len(local_entered_all),alpaca_entry_filled=len(entry_filled),alpaca_round_trips=len(closed),selection_rate=(len(local_entered)/len(activations_window) if activations_window else None),entry_fill_rate=(len(entry_filled)/len(local_entered) if local_entered else None),round_trip_rate=(len(closed)/len(entry_filled) if entry_filled else None),mirror_states=dict(Counter(r.get('status','UNKNOWN') for r in trades))),performance=dict(local_realized_net_pnl=sum(local_pnls),local_max_drawdown_fraction=max_dd(local_pnls),broker_realized_gross_pnl=sum(broker_pnls),broker_max_drawdown_fraction=max_dd(broker_pnls),mean_entry_slippage=None if not entry_slip else statistics.mean(entry_slip),mean_exit_slippage=None if not exit_slip else statistics.mean(exit_slip),positive_local_session_rate=(sum(v>0 for v in session_pnls)/len(session_pnls) if session_pnls else None),local_session_pnl_stdev=(statistics.pstdev(session_pnls) if len(session_pnls)>1 else 0.0)),by_session=dict(sorted(byday.items())),entry_filter_counterfactual=filter_value,notes=['Filter scenarios are counterfactual diagnostics and remain auto_apply=false.','Broker P&L is gross fill-to-fill unless fees are explicitly supplied by Alpaca.','No scientific rule is promoted or removed during the observation freeze.'])
target=A/'EXECUTION_FUNNEL_V01.json';tmp=target.with_suffix('.tmp');tmp.write_text(json.dumps(report,indent=2));tmp.replace(target)
print(json.dumps({'freeze':report['freeze']['status'],'funnel':report['funnel'],'performance':report['performance']},indent=2))
