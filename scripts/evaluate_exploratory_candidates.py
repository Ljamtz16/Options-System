import csv,json
from pathlib import Path
from options_system.episode_evaluation import evaluate_candidate_days

R=Path(__file__).resolve().parents[1]
cfg=json.loads((R/'artifacts/intraday/EXPLORATORY_HYPOTHESIS_CANDIDATES_V02.json').read_text(encoding='utf-8'))
with open(R/'data/processed/intraday/intraday_feature_lab_v01.csv',encoding='utf-8') as f:
    rows=list(csv.DictReader(f))
report={'version':'v0.1','status':'PROSPECTIVE_EVALUATION_ONLY','exclude_through':'2026-10-02','candidates':{}}
for candidate in cfg['candidates']:
    days=evaluate_candidate_days(rows,candidate,'2026-10-02')
    report['candidates'][candidate['id']]={'days':days,'prospective_days':len(days),'episodes':sum(d['episodes'] for d in days),'decided':sum(d['decided'] for d in days),'tp_first':sum(d['tp_first'] for d in days)}
out=R/'artifacts/intraday/EXPLORATORY_CANDIDATE_PROSPECTIVE_EVAL_V01.json'
out.write_text(json.dumps(report,indent=2),encoding='utf-8')
print('EVALUATED',len(report['candidates']))
