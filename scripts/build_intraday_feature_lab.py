import csv,json,statistics
from pathlib import Path
from options_system.intraday_feature_lab import build_feature_lab,write_csv

ROOT=Path(__file__).resolve().parents[1]
def read(p):return list(csv.DictReader(open(p,encoding='utf-8'))) if p.exists() else []
state=read(ROOT/'data/processed/prospective/prospective_market_state_v1.csv')
outcomes=read(ROOT/'data/processed/intraday/spy_intraday_outcomes_all_days.csv')
rows=build_feature_lab(state,outcomes,ROOT/'data/raw/prospective')
out=ROOT/'data/processed/intraday/intraday_feature_lab_v01.csv';write_csv(rows,out)
summary={'version':'v0.1','status':'EXPLORATORY_ONLY','rows':len(rows),'days':sorted({r['decision_date'] for r in rows}),
         'events':{}}
for side in ('call','put'):
 for h in (15,30,60):
  for event in ('mfe10','tp10_before_sl10'):
   k=f'label_{side}_{event}_{h}m';vals=[int(r[k]) for r in rows if r.get(k) not in (None,'')]
   summary['events'][k]={'n':len(vals),'positive':sum(vals),'rate':sum(vals)/len(vals) if vals else None}
p=ROOT/'artifacts/intraday/FEATURE_LAB_V01_SUMMARY.json';p.write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps(summary))
