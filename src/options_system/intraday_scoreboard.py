import csv, json, statistics
from collections import defaultdict
from pathlib import Path

HORIZONS=(15,30,60)
SIDES=("call","put")


def _f(v):
    try:return float(v)
    except (TypeError,ValueError):return None


def _summ(values):
    xs=[x for x in values if x is not None]
    if not xs:return {"n":0}
    return {"n":len(xs),"mean":sum(xs)/len(xs),
            "median":statistics.median(xs),
            "win_rate":sum(x>0 for x in xs)/len(xs),
            "gt10_rate":sum(x>=.10 for x in xs)/len(xs)}


def build_scoreboard(csv_path,out_json):
    rows=list(csv.DictReader(open(csv_path,encoding="utf-8")))
    groups=defaultdict(list)
    for r in rows:groups[r.get("symbol","UNKNOWN")].append(r)
    result={}
    for symbol,rs in sorted(groups.items()):
        item={"rows":len(rs),"horizons":{}}
        for h in HORIZONS:
            hs={}
            for side in SIDES:
                vals=[_f(r.get(f"{side}_terminal_return_{h}m")) for r in rs]
                d=_summ(vals)
                tp_key=f"{side}_{h}m_tp10_sl10"
                tp=[r.get(tp_key) for r in rs if r.get(tp_key)]
                if tp:
                    d["tp10_sl10_n"]=len(tp)
                    d["tp_first_rate"]=sum(x=="TP_FIRST" for x in tp)/len(tp)
                    d["sl_first_rate"]=sum(x=="SL_FIRST" for x in tp)/len(tp)
                hs[side]=d
            item["horizons"][str(h)]=hs
        result[symbol]=item
    Path(out_json).parent.mkdir(parents=True,exist_ok=True)
    Path(out_json).write_text(json.dumps(result,indent=2),encoding="utf-8")
    return result
