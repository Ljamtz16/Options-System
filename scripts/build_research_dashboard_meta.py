import json
from options_system.prospective_readiness import build_health
from pathlib import Path

R=Path(__file__).resolve().parents[1]
A=R/'artifacts/intraday'
frozen=json.loads((A/'FROZEN_HYPOTHESES_V02.json').read_text(encoding='utf-8'))
candidates=json.loads((A/'EXPLORATORY_HYPOTHESIS_CANDIDATES_V02.json').read_text(encoding='utf-8'))
combos=json.loads((A/'FEATURE_LAB_COMBINATIONS_V01.json').read_text(encoding='utf-8'))
eval_path=A/'EXPLORATORY_CANDIDATE_PROSPECTIVE_EVAL_V01.json'
evaluation=json.loads(eval_path.read_text(encoding='utf-8')) if eval_path.exists() else {'candidates':{}}
daily_path=A/'HYPOTHESIS_DAILY_REPORT_V02.json'
daily=json.loads(daily_path.read_text(encoding='utf-8')) if daily_path.exists() else {
    'version':'v0.2','days':{},'prospective_episodes':[],
    'virtual_account':{'initial_cash':1000.0,'final_cash':1000.0,'net_pnl':0.0,'ledger':[]}
}
sizing_path=A/'PROSPECTIVE_SIZING_COMPARISON_V01.json'
sizing=json.loads(sizing_path.read_text(encoding='utf-8')) if sizing_path.exists() else {
    'scientific_evidence':False,'purpose':'execution_and_risk_simulation_only','strategies':{}
}
stress_path=A/'PROSPECTIVE_STRESS_TEST_V01.json'
stress=json.loads(stress_path.read_text(encoding='utf-8')) if stress_path.exists() else {
    'scientific_evidence':False,'purpose':'deterministic_execution_risk_stress_testing_only','scenarios':{}
}
gate_path=A/'PROSPECTIVE_RISK_GATE_V01.json'
gate=json.loads(gate_path.read_text(encoding='utf-8')) if gate_path.exists() else {
    'status':'UNKNOWN','allowed_max_fraction':0,'recommended_strategy':'NO_TRADE'
}
execution_path=A/'PROSPECTIVE_EXECUTION_GATE_V01.json'
execution=json.loads(execution_path.read_text(encoding='utf-8')) if execution_path.exists() else {
    'counts':{'PASS':0,'BLOCK':0,'REVIEW_MISSING_MARKET_QUALITY':0},'episodes':[]
}
health=build_health(R)
(A/'SYSTEM_HEALTH_V01.json').write_text(json.dumps(health,indent=2),encoding='utf-8')
hypotheses=[]
for h in frozen['hypotheses']:
    hypotheses.append({'id':h['id'],'side':h['side'].upper(),'horizon_min':h['horizon_min'],
                       'status':'FROZEN · PROSPECTIVE','kind':'frozen','rules':h['rules']})
frozen_source_candidates={h.get('source_candidate') for h in frozen['hypotheses'] if h.get('source_candidate')}
frozen_ids={h['id'] for h in frozen['hypotheses']}
for h in candidates['candidates']:
    if h['id'] in frozen_ids or h['id'] in frozen_source_candidates:
        continue
    hypotheses.append({'id':h['id'],'side':h['side'].upper(),'horizon_min':h['horizon_min'],
                       'status':'EXPLORATORY · NOT FROZEN','kind':'candidate','rules':h['rules'],
                       'discovery_snapshot':h.get('discovery_snapshot'),'discovery_episode':h.get('discovery_episode')})
discovery={}
for label,payload in combos['labels'].items():
    discovery[label]={'top_stable':payload.get('top_stable',[])[:5]}
meta={'discovery_session':'2026-10-02','hypotheses':hypotheses,
      'prospective':evaluation.get('candidates',{}),'prospective_validation':daily,'sizing_simulation':sizing,'stress_testing':stress,'risk_gate':gate,'execution_gate':execution,'readiness':health,'discovery':discovery}
raw=json.dumps(meta,separators=(',',':'))
(A/'research_dashboard_meta.json').write_text(raw,encoding='utf-8')
(A/'research_dashboard_meta.js').write_text('window.RESEARCH_META='+raw+';',encoding='utf-8')
print('RESEARCH_META_OK',len(hypotheses),'prospective_episodes',len(daily.get('prospective_episodes',[])))
