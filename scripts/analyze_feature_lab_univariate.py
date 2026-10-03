import csv,json
from pathlib import Path
from options_system.feature_lab_scan import scan_univariate
ROOT=Path(__file__).resolve().parents[1]
rows=list(csv.DictReader(open(ROOT/'data/processed/intraday/intraday_feature_lab_v01.csv',encoding='utf-8')))
labels=['label_call_tp10_before_sl10_60m','label_put_tp10_before_sl10_15m',
        'label_call_mfe10_60m','label_put_mfe10_15m']
report={'version':'v0.1','status':'EXPLORATORY_ONLY','warning':'single-session feature discovery; not validation','labels':{}}
for lab in labels:
 x=scan_univariate(rows,lab,min_n=8)
 report['labels'][lab]={'top':x[:15]}
Path(ROOT/'artifacts/intraday/FEATURE_LAB_UNIVARIATE_V01.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
for lab in labels:
 print('\n',lab)
 for x in report['labels'][lab]['top'][:5]:
  print(x['feature'],x['op'],round(x['threshold'],6),x['n'],round(x['rate'],3),round(x['lift'],2))
