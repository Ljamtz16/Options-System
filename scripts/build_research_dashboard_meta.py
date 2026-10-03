import json
from pathlib import Path

R=Path(__file__).resolve().parents[1]
A=R/'artifacts/intraday'
frozen=json.loads((A/'FROZEN_HYPOTHESES_V02.json').read_text(encoding='utf-8'))
candidates=json.loads((A/'EXPLORATORY_HYPOTHESIS_CANDIDATES_V02.json').read_text(encoding='utf-8'))
combos=json.loads((A/'FEATURE_LAB_COMBINATIONS_V01.json').read_text(encoding='utf-8'))
eval_path=A/'EXPLORATORY_CANDIDATE_PROSPECTIVE_EVAL_V01.json'
evaluation=json.loads(eval_path.read_text(encoding='utf-8')) if eval_path.exists() else {'candidates':{}}
hypotheses=[]
for h in frozen['hypotheses']:
    hypotheses.append({'id':h['id'],'side':h['side'].upper(),'horizon_min':h['horizon_min'],'status':'FROZEN · PROSPECTIVE','kind':'frozen','rules':h['rules']})
frozen_source_candidates = {h.get('source_candidate') for h in frozen['hypotheses'] if h.get('source_candidate')}
frozen_ids = {h['id'] for h in frozen['hypotheses']}
for h in candidates['candidates']:
    if h['id'] in frozen_ids or h['id'] in frozen_source_candidates:
        continue
    hypotheses.append({'id':h['id'],'side':h['side'].upper(),'horizon_min':h['horizon_min'],'status':'EXPLORATORY · NOT FROZEN','kind':'candidate','rules':h['rules'],'discovery_snapshot':h.get('discovery_snapshot'),'discovery_episode':h.get('discovery_episode')})
discovery={}
for label,payload in combos['labels'].items():
    discovery[label]={'top_stable':payload.get('top_stable',[])[:5]}
meta={'discovery_session':'2026-10-02','hypotheses':hypotheses,'prospective':evaluation.get('candidates',{}),'discovery':discovery}
raw=json.dumps(meta,separators=(',',':'))
(A/'research_dashboard_meta.json').write_text(raw,encoding='utf-8')
(A/'research_dashboard_meta.js').write_text('window.RESEARCH_META='+raw+';',encoding='utf-8')
print('RESEARCH_META_OK',len(hypotheses))
