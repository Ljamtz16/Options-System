import csv,json
from pathlib import Path
from datetime import date,datetime
from .chain_features import extract_chain_features
from .option_surface import extract_option_surface

DELTA_FIELDS=("spot","atm_iv","put_call_iv_skew","put_call_volume_ratio_1pct","put_volume_share_1pct",
              "spy_from_open","qqq_from_open","iwm_from_open","qqq_minus_spy_from_open","iwm_minus_spy_from_open",
              "vix_current","vix_change_pct","sector_mean_from_open","sector_dispersion",
              "dte_1_3_25d_put_minus_call_iv","dte_4_7_25d_put_minus_call_iv","dte_8_10_25d_put_minus_call_iv")

def snapshot_to_row(path):
 obj=json.loads(Path(path).read_text(encoding="utf-8")); p=obj["payload"]
 md=date.fromisoformat(p["market_clock"]["timestamp"][:10])
 us=p["underlying"]["snapshot"]; trade=us.get("latestTrade") or {}; quote=us.get("latestQuote") or {}
 spot=trade.get("p") or (((quote.get("bp") or 0)+(quote.get("ap") or 0))/2 or None)
 rs=p["research_state"]; prob=rs["probability"]; act=rs["activity_gate"]; o6=rs["o6"]
 row={"capture_id":obj["capture_id"],"captured_at_utc":obj["captured_at_utc"],"schema_version":p.get("schema_version"),
      "decision_date":rs["features"]["decision_date"],"spot":spot,"open_t":rs["features"]["open_t"],
      "p_raw":prob["raw"],"p_calibrated":prob["calibrated"],"p_conservative":prob["conservative"],
      "activity_pass":act["activity_pass"],"o6_decision":o6["decision"],
      "direction":rs["direction"]["direction"],"source_file":Path(path).name}
 chain=p["options"]["snapshot"]
 row.update(extract_chain_features(chain,float(spot),md))
 row.update(extract_option_surface(chain,float(spot),md))
 for k,v in (((p.get("cross_market") or {}).get("features") or {})).items():row[k]=v
 for k,v in (((p.get("sectors") or {}).get("features") or {})).items():row[k]=v
 vix=p.get("vix") or {}
 row["vix_current"]=vix.get("current_price");row["vix_prev_close"]=vix.get("prev_day_close")
 row["vix_change"]=vix.get("change");row["vix_change_pct"]=vix.get("change_pct")
 row["vix_timestamp"]=vix.get("timestamp")
 for k,v in ((((p.get("intraday_context") or {}).get("SPY") or {}))).items():row[k]=v
 return row

def _num(x):
 try:return float(x)
 except (TypeError,ValueError):return None

def add_snapshot_deltas(rows):
 rows.sort(key=lambda r:r["captured_at_utc"]);prev_by_day={};first_by_day={}
 for r in rows:
  d=r["decision_date"];prev=prev_by_day.get(d);first=first_by_day.setdefault(d,r)
  if prev:
   t0=datetime.fromisoformat(prev["captured_at_utc"]);t1=datetime.fromisoformat(r["captured_at_utc"])
   r["minutes_since_prev"]=(t1-t0).total_seconds()/60
  else:r["minutes_since_prev"]=None
  for f in DELTA_FIELDS:
   cur=_num(r.get(f));pv=_num(prev.get(f)) if prev else None;fv=_num(first.get(f))
   r[f"d_{f}_prev"]=(cur-pv) if cur is not None and pv is not None else None
   r[f"d_{f}_since_first"]=(cur-fv) if cur is not None and fv is not None else None
  prev_by_day[d]=r
 return rows

def build_dataset(snapshot_dir,out_csv):
 files=sorted(Path(snapshot_dir).glob("spy_options_*.json"))
 rows=add_snapshot_deltas([snapshot_to_row(f) for f in files])
 if not rows:return 0
 fields=[]
 for r in rows:
  for k in r:
   if k not in fields:fields.append(k)
 Path(out_csv).parent.mkdir(parents=True,exist_ok=True)
 with open(out_csv,"w",newline="",encoding="utf-8") as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
 return len(rows)
