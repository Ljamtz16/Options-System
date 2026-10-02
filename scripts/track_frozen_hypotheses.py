import csv,json
from pathlib import Path
from options_system.prospective_hypothesis_tracker import load_hypotheses,annotate,write_tracker,summarize

ROOT=Path(__file__).resolve().parents[1]
state_p=ROOT/'data/processed/prospective/prospective_market_state_v1.csv'
outcomes_p=ROOT/'data/processed/intraday/spy_intraday_outcomes_all_days.csv'
hyp_p=ROOT/'artifacts/intraday/FROZEN_HYPOTHESES_V01.json'
out_p=ROOT/'data/processed/intraday/prospective_hypothesis_tracker_v01.csv'
rep_p=ROOT/'artifacts/intraday/PROSPECTIVE_HYPOTHESIS_REPORT_V01.json'

def load_csv(p):
    return list(csv.DictReader(open(p,encoding='utf-8'))) if p.exists() else []

meta=json.loads(hyp_p.read_text(encoding='utf-8'));freeze=meta['frozen_at']
h=meta['hypotheses'];state=load_csv(state_p);outs=load_csv(outcomes_p)
by_ts={r['captured_at_utc']:r for r in outs}
rows=[]
for s in state:
    x=dict(s);x.update(by_ts.get(s['captured_at_utc'],{}));rows.append(x)
rows=annotate(rows,h);write_tracker(rows,out_p)
pre=[r for r in rows if r.get('decision_date','')<=freeze]
post=[r for r in rows if r.get('decision_date','')>freeze]
rep={'version':'v0.1','frozen_at':freeze,'pre_freeze_diagnostic':summarize(pre,h),
     'prospective_only':summarize(post,h),'prospective_rows':len(post)}
rep_p.write_text(json.dumps(rep,indent=2),encoding='utf-8')
print(json.dumps(rep))
