import csv,json
from pathlib import Path
from datetime import datetime,date
from .intraday_universe import INTRADAY_HORIZONS_MIN
from .chain_features import extract_chain_features
from .option_surface import extract_option_surface
from .intraday_contracts import representative_contracts,conservative_long_pnl

def _load(path):
    obj=json.loads(Path(path).read_text(encoding="utf-8"))
    return obj,obj["payload"]

def _target_snapshot(snaps,base_ts,minutes):
    target=base_ts.timestamp()+minutes*60
    candidates=[]
    for x in snaps:
        dt=x["ts"].timestamp()
        if target<=dt<=target+6*60:candidates.append((dt,x))
    return min(candidates,key=lambda z:z[0])[1] if candidates else None

def _add_context(row,p):
    gc=p.get("global_context") or {}
    vix=gc.get("vix") or {}
    row["vix_current"]=vix.get("current_price")
    row["vix_change_pct"]=vix.get("change_pct")
    row.update({f"sector_{k}":v for k,v in (gc.get("sectors") or {}).items()})
    row.update({f"market_{k}":v for k,v in (gc.get("cross_market") or {}).items()})

def build_intraday_dataset(snapshot_dir,out_csv):
    raw=[]
    for f in sorted(Path(snapshot_dir).glob("intraday_options_*.json")):
        obj,p=_load(f)
        ts=datetime.fromisoformat(obj["captured_at_utc"])
        raw.append({"file":f,"obj":obj,"payload":p,"ts":ts})
    rows=[]
    for base in raw:
        p=base["payload"];md=date.fromisoformat(p["market_date"])
        same_day=[x for x in raw if x["payload"].get("market_date")==p["market_date"]]
        for symbol,rec in (p.get("symbols") or {}).items():
            chain=rec["option_snapshot"];spot=float(rec["spot"])
            row={"captured_at_utc":base["obj"]["captured_at_utc"],
                 "market_date":p["market_date"],"symbol":symbol,
                 "spot":spot,"source_file":base["file"].name}
            _add_context(row,p)
            row.update(extract_chain_features(chain,spot,md))
            row.update(extract_option_surface(chain,spot,md))
            reps=representative_contracts(chain,md)
            for side in ("call","put"):
                ent=reps.get(side)
                row[f"entry_{side}_contract"]=ent["symbol"] if ent else None
                row[f"entry_{side}_ask"]=ent["ask"] if ent else None
            for h in INTRADAY_HORIZONS_MIN:
                fut=_target_snapshot(same_day,base["ts"],h)
                _add_horizon(row,h,symbol,spot,reps,fut)
            _add_eod(row,symbol,spot,reps,same_day,base["ts"])
            rows.append(row)
    return _write(rows,out_csv)

def _add_horizon(row,h,symbol,spot,reps,fut):
    if not fut or symbol not in (fut["payload"].get("symbols") or {}):return
    r=fut["payload"]["symbols"][symbol];fspot=float(r["spot"])
    row[f"ret_{h}m"]=fspot/spot-1
    row[f"up_{h}m"]=fspot>spot
    for side in ("call","put"):
        pnl=conservative_long_pnl(reps.get(side),r["option_snapshot"])
        if pnl:
            row[f"{side}_pnl_{h}m_usd"]=pnl["pnl_usd"]
            row[f"{side}_ret_{h}m"]=pnl["return"]
            row[f"{side}_exit_bid_{h}m"]=pnl["exit_bid"]

def _add_eod(row,symbol,spot,reps,same_day,base_ts):
    later=[x for x in same_day if x["ts"]>base_ts and symbol in (x["payload"].get("symbols") or {})]
    if not later:return
    fut=max(later,key=lambda x:x["ts"]);r=fut["payload"]["symbols"][symbol]
    fspot=float(r["spot"]);row["ret_eod"]=fspot/spot-1
    row["up_eod"]=fspot>spot;row["eod_capture_utc"]=fut["obj"]["captured_at_utc"]
    for side in ("call","put"):
        pnl=conservative_long_pnl(reps.get(side),r["option_snapshot"])
        if pnl:
            row[f"{side}_pnl_eod_usd"]=pnl["pnl_usd"]
            row[f"{side}_ret_eod"]=pnl["return"]

def _write(rows,out_csv):
    if not rows:return 0
    fields=[]
    for r in rows:
        for k in r:
            if k not in fields:fields.append(k)
    Path(out_csv).parent.mkdir(parents=True,exist_ok=True)
    with open(out_csv,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields)
        w.writeheader();w.writerows(rows)
    return len(rows)
