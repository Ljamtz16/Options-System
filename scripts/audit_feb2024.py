import json
from pathlib import Path
base=Path("data/raw/historical/downloader_v1/2024-02")
mr=json.load(open(base/"month_summary.json"))
eligible=pages=bars=withbars=unexpected=0; sessions=0
for row in mr:
    if row.get("skipped"): continue
    d=row["date"]; sessions+=1; eligible+=row["eligible"]
    m=json.load(open(Path("data/raw/historical/backfill_v01/2024-02/manifests")/d/"universe.json"))
    exp={x["option_symbol"] for x in m["universe"]}; seen=set()
    for p in (base/d).glob("batch_*_page_*.json"):
        x=json.load(open(p)); pages+=1
        b=x["payload"].get("bars",{}); seen.update(b)
        bars+=sum(len(v) for v in b.values())
    withbars+=len(seen); unexpected+=len(seen-exp)
size=sum(p.stat().st_size for p in base.rglob("*") if p.is_file())
print(json.dumps({"sessions":sessions,"eligible_contract_sessions":eligible,
 "symbols_with_bars_sum":withbars,"raw_pages":pages,"bar_records":bars,
 "unexpected_symbols":unexpected,"bytes":size},indent=2))
