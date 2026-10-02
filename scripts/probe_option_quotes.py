from pathlib import Path
from options_system.env import load_local_env
from options_system.alpaca_history import fetch_json, save_snapshot

load_local_env()
symbol = "SPY260930C00760000"
params = {
    "symbols": symbol,
    "start": "2026-09-29T14:30:00Z",
    "end": "2026-09-29T15:00:00Z",
    "limit": 1000,
}
payload, url = fetch_json("quotes", params)
out = Path("data/raw/alpaca_spy260930c00760000_quotes_probe.json")
meta = save_snapshot(payload, url, out)
quotes = payload.get("quotes", {}).get(symbol, [])
print(f"records={len(quotes)}")
print(f"sha256={meta['sha256']}")
if quotes:
    print(f"first={quotes[0]}")
    print(f"last={quotes[-1]}")
