#!/usr/bin/env python3
from __future__ import annotations
import argparse,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'scripts/run_options_alpaca_mirror.py'

def main():
 ap=argparse.ArgumentParser(description='Dedicated Meta portfolio Alpaca Paper mirror')
 ap.add_argument('--check-account',action='store_true'); a=ap.parse_args()
 cmd=[sys.executable,str(BASE),'--env-file',str(Path.home()/'.config/options-system/meta-alpaca-paper.env'),
      '--local-state',str(ROOT/'artifacts/intraday/META_PORTFOLIO_LIVE_STATE_V01.json'),
      '--mirror-state',str(ROOT/'artifacts/intraday/META_ALPACA_PAPER_STATE_V01.json'),
      '--lock-file',str(ROOT/'artifacts/intraday/.meta_alpaca_mirror.lock'),'--no-default-put-confirm']
 if a.check_account:cmd.append('--check-account')
 return subprocess.call(cmd,cwd=ROOT)
if __name__=='__main__':raise SystemExit(main())
