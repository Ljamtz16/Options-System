import argparse
from pathlib import Path
from options_system.env import load_local_env
from options_system.alpaca_history import fetch_json, save_snapshot

load_local_env()
p = argparse.ArgumentParser()
p.add_argument("--symbol", required=True)
p.add_argument("--start", required=True)
p.add_argument("--end", required=True)
p.add_argument("--kind", choices=["bars", "trades"], default="bars")
p.add_argument("--out", required=True)
args = p.parse_args()
params = {"symbols": args.symbol, "start": args.start, "end": args.end, "limit": 1000}
if args.kind == "bars":
    params["timeframe"] = "1Min"
payload, url = fetch_json(args.kind, params)
meta = save_snapshot(payload, url, Path(args.out))
print(f"saved={args.out}")
print(f"sha256={meta['sha256']}")
print(f"top_level_keys={','.join(payload.keys())}")
