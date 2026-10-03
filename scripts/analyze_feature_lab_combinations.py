import csv,json
from pathlib import Path
from options_system.feature_lab_combinations import scan_combinations
R=Path(__file__).resolve().parents[1]
rows=list(csv.DictReader(open(R/'data/processed/intraday/intraday_feature_lab_v01.csv',encoding='utf-8')))
labels=['label_call_tp10_before_sl10_60m','label_put_tp10_before_sl10_15m']
report={'version':'v0.1','status':'EXPLORATORY_ONLY','labels':{}}
for label in labels:
    found=scan_combinations(rows,label)
    report['labels'][label]={'top_stable':[x for x in found if x['temporal_support']][:20],'top_any':found[:20]}
(R/'artifacts/intraday/FEATURE_LAB_COMBINATIONS_V01.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
for label in labels:
    print(label)
    for x in report['labels'][label]['top_stable'][:5]: print(json.dumps(x))
