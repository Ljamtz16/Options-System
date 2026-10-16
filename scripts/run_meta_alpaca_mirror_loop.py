#!/usr/bin/env python3
from __future__ import annotations
import subprocess,sys,time
from datetime import datetime,time as dtime,timezone
from pathlib import Path
from zoneinfo import ZoneInfo
ROOT=Path(__file__).resolve().parents[1]; RUN=ROOT/'scripts/run_meta_alpaca_mirror.py'; NY=ZoneInfo('America/New_York')
def in_window():
 n=datetime.now(timezone.utc).astimezone(NY); t=n.time().replace(tzinfo=None); return n.weekday()<5 and dtime(9,25)<=t<=dtime(16,5)
def main():
 print('META_ALPACA_WATCHER_STARTED interval=15s',flush=True)
 while True:
  if in_window():
   t=time.monotonic(); p=subprocess.run([sys.executable,str(RUN)],cwd=ROOT,text=True,capture_output=True)
   out=(p.stdout or '').strip(); err=(p.stderr or '').strip()
   if p.returncode or ('ACTION ' in out):
    if out:print(out,flush=True)
    if err:print(err,flush=True)
   time.sleep(max(1,15-(time.monotonic()-t)))
  else:time.sleep(60)
if __name__=='__main__':raise SystemExit(main())
