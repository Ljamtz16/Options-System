import json,sys
from pathlib import Path
from options_system.quality_gate import quality_session
month=sys.argv[1]; mans=Path(sys.argv[2]); raw=Path("data/raw/historical/downloader_v1")/month
rows=[]
for d in sorted(p.name for p in raw.iterdir() if p.is_dir()):
 q=quality_session(raw/d,mans/d/"universe.json"); q["date"]=d; rows.append(q)
 print(d,q["status"],q["bar_rows"],q["reasons"],flush=True)
out=Path("data/processed/quality_v1")/month; out.mkdir(parents=True,exist_ok=True)
(out/"quality_report.json").write_text(json.dumps(rows,indent=2))
print("PASS",sum(x["status"]=="PASS" for x in rows),"FAIL",sum(x["status"]!="PASS" for x in rows))
