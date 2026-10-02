import csv
from datetime import date,timedelta
from pathlib import Path
from .spy_daily import fetch_daily_spy
from .prospective_collector import market_clock,market_date_from_clock

def _completed_daily_rows(d):
 clock=market_clock(); market_date=market_date_from_clock(clock)
 end=(market_date+timedelta(days=1)).isoformat()+"T00:00:00Z"
 rows=fetch_daily_spy(d.isoformat()+"T00:00:00Z",end)
 rows=[r for r in rows if r["date"]>=d.isoformat()]
 if clock.get("is_open"):
  rows=[r for r in rows if r["date"]<market_date.isoformat()]
 return rows

def _labels_for_date(d):
 rows=_completed_daily_rows(d)
 if not rows or rows[0]["date"]!=d.isoformat():return {}
 o=float(rows[0]["open"]);out={}
 for h in (1,3):
  if len(rows)<h:continue
  seg=rows[:h];last=seg[-1]
  mfe=max(float(x["high"])/o-1 for x in seg);mae=min(float(x["low"])/o-1 for x in seg)
  out.update({f"h{h}_terminal_return":float(last["close"])/o-1,f"h{h}_mfe":mfe,f"h{h}_mae":mae,
              f"h{h}_path_1pct":max(mfe,-mae)>=.01,f"h{h}_up":float(last["close"])>o,
              f"h{h}_label_end":last["date"]})
 return out

def label_dataset(in_csv,out_csv):
 rows=list(csv.DictReader(open(in_csv,encoding="utf-8")));cache={}
 for r in rows:
  d=date.fromisoformat(r["decision_date"])
  if d not in cache:cache[d]=_labels_for_date(d)
  r.update(cache[d])
 fields=[]
 for r in rows:
  for k in r:
   if k not in fields:fields.append(k)
 Path(out_csv).parent.mkdir(parents=True,exist_ok=True)
 with open(out_csv,"w",newline="",encoding="utf-8") as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
 return len(rows)
