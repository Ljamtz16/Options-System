import json
from pathlib import Path
d="2024-02-09"
u=json.load(open(f"data/raw/historical/backfill_v01/2024-02/manifests/{d}/universe.json"))
expected={r["option_symbol"] for r in u["universe"]}
root=Path(f"data/raw/historical/downloader_v1/2024-02/{d}")
seen=set(); pages=0; records=0
for p in root.glob("batch_*_page_*.json"):
    x=json.load(open(p)); pages+=1
    bars=x["payload"].get("bars",{})
    seen.update(bars.keys()); records+=sum(len(v) for v in bars.values())
print("expected",len(expected),"symbols_with_bars",len(seen),"zero_activity",len(expected-seen),
      "pages",pages,"bar_records",records,"unexpected",len(seen-expected))
