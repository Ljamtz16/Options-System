import csv,json,sys
from pathlib import Path
from options_system.normalizer import normalize_session,FIELDS
month=sys.argv[1]; mans=Path(sys.argv[2]); raw=Path("data/raw/historical/downloader_v1")/month
out=Path("data/processed/options_bars_v1")/month; out.mkdir(parents=True,exist_ok=True); total=0
for s in sorted(p.name for p in raw.iterdir() if p.is_dir()):
 rows=normalize_session(raw/s,mans/s/"universe.json"); total+=len(rows); f=out/f"{s}.csv"
 with f.open("w",newline="",encoding="utf-8") as h:
  w=csv.DictWriter(h,fieldnames=FIELDS); w.writeheader(); w.writerows(rows)
 print(s,len(rows),flush=True)
(out/"manifest.json").write_text(json.dumps({"month":month,"rows":total,"sessions":len(list(out.glob("*.csv"))),"manifest_root":str(mans)},indent=2))
print("TOTAL",month,total,flush=True)
