import json,sys
from pathlib import Path
month=sys.argv[1]; base=Path("data/raw/historical/downloader_v1")/month
mr=json.load(open(base/"month_summary.json")); eligible=pages=bars=withbars=unexpected=0
for row in mr:
 d=row["date"]; eligible+=row["eligible"]
 m=json.load(open(Path("data/raw/historical/manifests_v1")/month/d/"universe.json"))
 exp={x["option_symbol"] for x in m["universe"]}; seen=set()
 for p in (base/d).glob("batch_*_page_*.json"):
  x=json.load(open(p)); pages+=1; b=x["payload"].get("bars",{}); seen.update(b); bars+=sum(len(v) for v in b.values())
 withbars+=len(seen); unexpected+=len(seen-exp)
size=sum(p.stat().st_size for p in base.rglob("*") if p.is_file())
print(json.dumps({"month":month,"sessions":len(mr),"eligible_contract_sessions":eligible,
"symbols_with_bars_sum":withbars,"zero_activity":eligible-withbars,"raw_pages":pages,
"bar_records":bars,"unexpected_symbols":unexpected,"bytes":size},indent=2))
