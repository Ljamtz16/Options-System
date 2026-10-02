import argparse
from pathlib import Path
from options_system.env import load_local_env
from options_system.historical_backfill import fetch_pages

load_local_env()
p=argparse.ArgumentParser()
p.add_argument("--symbol",required=True)
p.add_argument("--start",required=True)
p.add_argument("--end",required=True)
p.add_argument("--out",required=True)
args=p.parse_args()
base=Path(args.out)
for kind in ("bars","trades"):
    m=fetch_pages(kind,args.symbol,args.start,args.end,base/kind)
    print(kind,"pages=",m["pages"],"records=",m["records"])
