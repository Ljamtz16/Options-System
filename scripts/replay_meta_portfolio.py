#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from options_system.meta_portfolio import replay,ART

def main():
 ap=argparse.ArgumentParser(description='Replay Meta+TTT ranked paper portfolio')
 ap.add_argument('--date')
 ap.add_argument('--start-cash',type=float,default=1000.0)
 ap.add_argument('--ranking-window-seconds',type=int,default=90)
 ap.add_argument('--no-daily-halt',action='store_true')
 ap.add_argument('--output',default=str(ART/'META_PORTFOLIO_REPLAY_V01.json'))
 a=ap.parse_args()
 if not a.date:
  dates=sorted(x.stem for x in (ROOT/'data/processed/intraday/sessions').glob('20*.csv'))
  a.date=dates[-1] if dates else None
 if not a.date: raise SystemExit('No session date available')
 out=replay(a.date,a.start_cash,a.ranking_window_seconds,None if a.no_daily_halt else .10)
 Path(a.output).write_text(json.dumps(out,indent=2,default=str)+'\n')
 print(json.dumps(out['summary'],indent=2))
 for t in out['trades']:
  print(t['entry_time'],t['source'],t['symbol'],t['exit_reason'],f"{t['net_pnl']:.2f}",f"cash={t['cash_after']:.2f}",t['episode_id'])
 print('OUTPUT',Path(a.output).resolve())
 return 0
if __name__=='__main__': raise SystemExit(main())
