import csv,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
track=ROOT/'data/processed/intraday/prospective_hypothesis_tracker_v01.csv'
out=ROOT/'artifacts/intraday/HYPOTHESIS_DAILY_REPORT_V01.json'
rows=list(csv.DictReader(open(track,encoding='utf-8'))) if track.exists() else []
days=sorted({r.get('decision_date') for r in rows if r.get('decision_date')})
report={}
for day in days:
    dr=[r for r in rows if r.get('decision_date')==day]
    activations=[]
    for r in dr:
        for hid in [x for x in (r.get('active_hypotheses') or '').split(';') if x]:
            side='call' if 'CALL_' in hid else 'put';h=60 if 'CALL_' in hid else 15
            key=f'{side}_ret_{h}m'
            activations.append({'hypothesis':hid,'captured_at_utc':r.get('captured_at_utc'),
                                'side':side,'horizon_min':h,'spot':r.get('spot'),
                                'contract':r.get(f'{side}_contract'),
                                'entry_ask':r.get(f'{side}_entry_ask'),
                                'return':r.get(key),
                                'mfe':r.get(f'{side}_mfe_{h}m'),
                                'mae':r.get(f'{side}_mae_{h}m'),
                                'tp10_sl10':r.get(f'{side}_{h}m_tp10_sl10')})
    report[day]={'snapshots':len(dr),'activations':activations}
out.write_text(json.dumps({'version':'v0.1','days':report},indent=2),encoding='utf-8')
print(f'HYPOTHESIS_REPORT days={len(days)} activations={sum(len(x["activations"]) for x in report.values())}')
