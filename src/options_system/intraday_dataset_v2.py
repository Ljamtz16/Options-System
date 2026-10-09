import csv,json
from pathlib import Path
from datetime import datetime,date,timedelta
from .intraday_universe import INTRADAY_HORIZONS_MIN
from .chain_features import extract_chain_features
from .option_surface import extract_option_surface
from .intraday_contracts import representative_contracts,conservative_long_pnl
from .intraday_outcomes import path_outcomes,contract_path_outcomes
from .intraday_targets import option_trade_targets,direct_profit_targets

def _load(path):
    obj=json.loads(Path(path).read_text(encoding="utf-8"))
    return obj,obj["payload"]

def _context(row,p):
    gc=p.get("global_context") or {};v=gc.get("vix") or {}
    row["vix_current"]=v.get("current_price")
    row["vix_change_pct"]=v.get("change_pct")
    row.update({f"sector_{k}":x for k,x in (gc.get("sectors") or {}).items()})
    row.update({f"market_{k}":x for k,x in (gc.get("cross_market") or {}).items()})

def _window(snaps,base_ts,minutes,symbol):
    end=base_ts+timedelta(minutes=minutes)
    return [x for x in snaps if base_ts<x["ts"]<=end+timedelta(minutes=6)
            and symbol in (x["payload"].get("symbols") or {})]
def _decorate_horizon(row,h,symbol,entry_spot,reps,window):
    if not window:return
    spots=[];chains=[]
    for x in window:
        rec=x["payload"]["symbols"][symbol]
        spots.append(float(rec["spot"]));chains.append(rec["option_snapshot"])
    po=path_outcomes(spots,entry_spot)
    for k,v in po.items():row[f"{k}_{h}m"]=v
    for side in ("call","put"):
        co=contract_path_outcomes(reps.get(side),chains)
        for k,v in co.items():row[f"{side}_{k}_{h}m"]=v
        path=[];ent=reps.get(side)
        if ent:
            for ch in chains:
                pnl=conservative_long_pnl(ent,ch)
                if pnl:path.append(pnl["return"])
        row.update(option_trade_targets(path,f"{side}_{h}m"))
        terminal=co.get("terminal_return") if co else None
        row.update(direct_profit_targets(terminal,f"{side}_{h}m"))

def _decorate_eod(row,symbol,entry_spot,reps,same_day,base_ts):
    later=[x for x in same_day if x["ts"]>base_ts and symbol in (x["payload"].get("symbols") or {})]
    if not later:return
    spots=[float(x["payload"]["symbols"][symbol]["spot"]) for x in later]
    chains=[x["payload"]["symbols"][symbol]["option_snapshot"] for x in later]
    for k,v in path_outcomes(spots,entry_spot).items():row[f"{k}_eod"]=v
    for side in ("call","put"):
        co=contract_path_outcomes(reps.get(side),chains)
        for k,v in co.items():row[f"{side}_{k}_eod"]=v
        path=[];ent=reps.get(side)
        if ent:
            for ch in chains:
                pnl=conservative_long_pnl(ent,ch)
                if pnl:path.append(pnl["return"])
        row.update(option_trade_targets(path,f"{side}_eod"))
        row.update(direct_profit_targets(co.get("terminal_return") if co else None,f"{side}_eod"))
def build_intraday_dataset_v2(snapshot_dir,out_csv):
    # Keep option chains for only one market session in memory.
    files=sorted(Path(snapshot_dir).glob("intraday_options_*.json"))
    groups={}
    for f in files:
        obj,p=_load(f)
        groups.setdefault(p["market_date"],[]).append(f)
        del obj,p
    rows_by_file={}
    for day_files in groups.values():
        raw=[]
        for f in day_files:
            obj,p=_load(f)
            raw.append({"file":f,"obj":obj,"payload":p,
                        "ts":datetime.fromisoformat(obj["captured_at_utc"])})
        del obj,p
        for row in _build_day_rows(raw):
            rows_by_file.setdefault(row["source_file"],[]).append(row)
        del raw
    # Preserve the original file/symbol order and column discovery order.
    rows=[row for f in files for row in rows_by_file.get(f.name,[])]
    return _write(rows,out_csv)

def _build_day_rows(raw):
    rows=[]
    for base in raw:
        p=base["payload"];md=date.fromisoformat(p["market_date"])
        same_day=[x for x in raw if x["payload"].get("market_date")==p["market_date"]]
        for symbol,rec in (p.get("symbols") or {}).items():
            chain=rec["option_snapshot"];spot=float(rec["spot"])
            row={"captured_at_utc":base["obj"]["captured_at_utc"],
                 "market_date":p["market_date"],"symbol":symbol,
                 "spot":spot,"source_file":base["file"].name}
            _context(row,p)
            row.update(extract_chain_features(chain,spot,md))
            row.update(extract_option_surface(chain,spot,md))
            reps=representative_contracts(chain,md)
            for side in ("call","put"):
                ent=reps.get(side)
                row[f"entry_{side}_contract"]=ent["symbol"] if ent else None
                row[f"entry_{side}_ask"]=ent["ask"] if ent else None
                row[f"entry_{side}_delta"]=ent["delta"] if ent else None
                row[f"entry_{side}_dte"]=ent["dte"] if ent else None
            for h in INTRADAY_HORIZONS_MIN:
                _decorate_horizon(row,h,symbol,spot,reps,_window(same_day,base["ts"],h,symbol))
            _decorate_eod(row,symbol,spot,reps,same_day,base["ts"])
            rows.append(row)
    return rows

def _write(rows,out_csv):
    if not rows:return 0
    fields=[]
    for r in rows:
        for k in r:
            if k not in fields:fields.append(k)
    Path(out_csv).parent.mkdir(parents=True,exist_ok=True)
    with open(out_csv,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    return len(rows)