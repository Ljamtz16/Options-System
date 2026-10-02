import csv,json
from collections import defaultdict
from pathlib import Path

p=Path('data/processed/intraday/intraday_options_v2.csv')
rows=list(csv.DictReader(open(p,encoding='utf-8'))) if p.exists() else []
by_day=defaultdict(list)
for r in rows:by_day[r.get('market_date')].append(r)
out={}
for day,rs in sorted(by_day.items()):
    symbols=sorted({r.get('symbol') for r in rs if r.get('symbol')})
    out[day]={"rows":len(rs),"symbols":symbols}
    for sym in symbols:
        ss=[r for r in rs if r.get('symbol')==sym]
        def best(field):
            vals=[]
            for r in ss:
                try: vals.append((float(r[field]),r.get('captured_at_utc')))
                except: pass
            return max(vals) if vals else None
        out[day][sym]={"best_call_30m":best('call_best_return_30m'),
                       "best_put_30m":best('put_best_return_30m')}
Path('artifacts/intraday').mkdir(parents=True,exist_ok=True)
Path('artifacts/intraday/INTRADAY_DAILY_REPORT.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps(out,indent=2))