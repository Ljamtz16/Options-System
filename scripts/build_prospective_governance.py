import csv,json
from pathlib import Path
from options_system.prospective_governance import session_manifest,daily_rows,scoreboard

ROOT=Path(__file__).resolve().parents[1]
track=ROOT/'data/processed/intraday/prospective_hypothesis_tracker_v01.csv'
hyp=ROOT/'artifacts/intraday/FROZEN_HYPOTHESES_V01.json'
daily_p=ROOT/'data/processed/intraday/prospective_hypothesis_daily_v01.csv'
score_p=ROOT/'artifacts/intraday/PROSPECTIVE_SCOREBOARD_V01.json'
manifest_dir=ROOT/'artifacts/intraday/session_manifests'

meta=json.loads(hyp.read_text(encoding='utf-8'))
rows=list(csv.DictReader(open(track,encoding='utf-8'))) if track.exists() else []
daily=daily_rows(rows,meta['hypotheses'],meta['frozen_at'])
daily_p.parent.mkdir(parents=True,exist_ok=True)
fields=['decision_date','hypothesis','activated','n_signals','first_signal_utc','mean_return',
        'best_mfe','worst_mae','tp_first','sl_first','daily_result']
with open(daily_p,'w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(daily)
score={'version':'v0.1','frozen_at':meta['frozen_at'],'review_days':[5,10,20,30],
       'hypotheses':scoreboard(daily,meta['hypotheses'])}
score_p.write_text(json.dumps(score,indent=2),encoding='utf-8')
manifest_dir.mkdir(parents=True,exist_ok=True)
for day in sorted({r.get('decision_date') for r in rows if r.get('decision_date')}):
    dr=[r for r in rows if r.get('decision_date')==day]
    m=session_manifest(meta,day,dr)
    (manifest_dir/f'{day}.json').write_text(json.dumps(m,indent=2),encoding='utf-8')
print(f'PROSPECTIVE_GOVERNANCE days={len({r["decision_date"] for r in daily})} daily_rows={len(daily)}')
