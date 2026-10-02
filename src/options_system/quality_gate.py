import json
from pathlib import Path

def quality_session(raw_dir,universe_manifest):
    m=json.loads(Path(universe_manifest).read_text()); expected={x["option_symbol"] for x in m["universe"]}
    seen=set(); rows=0; timestamps=[]; pages=0
    for p in sorted(Path(raw_dir).glob("batch_*_page_*.json")):
        pages+=1; x=json.loads(p.read_text()); bars=x["payload"].get("bars",{})
        seen.update(bars)
        for vals in bars.values():
            rows+=len(vals); timestamps.extend(v["t"] for v in vals)
    unexpected=sorted(seen-expected)
    duplicate_rows=0
    keys=set()
    for p in sorted(Path(raw_dir).glob("batch_*_page_*.json")):
        bars=json.loads(p.read_text())["payload"].get("bars",{})
        for s,vals in bars.items():
            for v in vals:
                k=(s,v["t"])
                if k in keys: duplicate_rows+=1
                keys.add(k)
    reasons=[]
    if not expected: reasons.append("EMPTY_CAUSAL_UNIVERSE")
    if pages==0: reasons.append("NO_RAW_PAGES")
    if expected and rows==0: reasons.append("ZERO_BARS_FOR_NONEMPTY_UNIVERSE")
    if unexpected: reasons.append("UNEXPECTED_SYMBOLS")
    if duplicate_rows: reasons.append("DUPLICATE_SYMBOL_TIMESTAMP")
    return {"status":"PASS" if not reasons else "QUALITY_FAIL","reasons":reasons,
      "eligible":len(expected),"symbols_with_bars":len(seen),"zero_bar_symbols":len(expected-seen),
      "bar_rows":rows,"raw_pages":pages,"unexpected_symbols":len(unexpected),"duplicate_rows":duplicate_rows}
