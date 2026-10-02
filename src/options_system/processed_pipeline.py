import csv,json
from pathlib import Path
from .quality_gate import quality_session
from .normalizer import normalize_session,FIELDS

def process_month(month,raw_root,manifest_root,processed_root):
    raw=Path(raw_root)/month; mans=Path(manifest_root)/month
    out=Path(processed_root)/month; out.mkdir(parents=True,exist_ok=True)
    report=[]; total=0
    for d in sorted(p.name for p in raw.iterdir() if p.is_dir()):
        q=quality_session(raw/d,mans/d/"universe.json"); q["date"]=d
        if q["status"]=="PASS":
            rows=normalize_session(raw/d,mans/d/"universe.json")
            if len(rows)!=q["bar_rows"]: raise ValueError(f"Count mismatch {d}")
            f=out/f"{d}.csv"
            with f.open("w",newline="",encoding="utf-8") as h:
                w=csv.DictWriter(h,fieldnames=FIELDS); w.writeheader(); w.writerows(rows)
            q["processed_rows"]=len(rows); total+=len(rows)
        else:
            q["processed_rows"]=0
        report.append(q)
    summary={"month":month,"sessions":len(report),"pass":sum(x["status"]=="PASS" for x in report),
      "fail":sum(x["status"]!="PASS" for x in report),"processed_rows":total,"sessions_detail":report}
    (out/"pipeline_manifest.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    return summary
