from options_system.dashboard_sessions import publish_meta_views
import os
import json
import sqlite3
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

tracker_path=A/'PROSPECTIVE_HYPOTHESIS_REPORT_V02.json'
tracker_summary=json.loads(tracker_path.read_text(encoding='utf-8')) if tracker_path.exists() else {
    'version':'v0.2',
    'frozen_at':frozen.get('frozen_at'),
    'pre_freeze_diagnostic':{},
    'prospective_only':{},
    'prospective_rows':0
}

paper_state_path=A/'PAPER_TRADING_LIVE_STATE_V01.json'
paper_state=json.loads(paper_state_path.read_text(encoding='utf-8')) if paper_state_path.exists() else {
    'mode':'LIVE_PAPER','initial_cash':1000.0,'cash':1000.0,
    'equity':1000.0,'net_account_pnl':0.0,'open_positions':[],
    'live_ledger':[],'causal_replay_summary':{}
}

options_alpaca_path=A/'OPTIONS_ALPACA_PAPER_STATE_V01.json'
options_alpaca=json.loads(options_alpaca_path.read_text(encoding='utf-8')) if options_alpaca_path.exists() else {
    'mode':'ALPACA_PAPER_MIRROR','paper_only':True,'submit_orders':False,
    'shadow_capital':1000.0,'account':{},'trades':{},'last_actions':[]
}

jev_root=R.parent/'jev-lab'
jev_paper_status_path=jev_root/'data/paper-status.json'
jev_paper_status=json.loads(jev_paper_status_path.read_text(encoding='utf-8')) if jev_paper_status_path.exists() else {}
jev_paper_orders=[]
jev_paper_db=jev_root/'data/paper.sqlite'
if jev_paper_db.exists():
    try:
        with sqlite3.connect(str(jev_paper_db),timeout=2) as db:
            rows=db.execute('SELECT * FROM intents ORDER BY rowid DESC LIMIT 100').fetchall()
        for cid,body,broker,state,created in rows:
            request=json.loads(body) if body else {}
            saved=json.loads(broker) if broker else {}
            jev_paper_orders.append({
                'client_order_id':cid,'created_at':created,'state':state,
                'symbol':request.get('symbol'),'qty':request.get('qty'),
                'side':request.get('side'),'position_intent':request.get('position_intent'),
                'type':request.get('type'),'limit_price':request.get('limit_price'),
                'broker_status':saved.get('status'),'filled_qty':saved.get('filled_qty'),
                'filled_avg_price':saved.get('filled_avg_price'),'filled_at':saved.get('filled_at')
            })
    except (sqlite3.Error,ValueError,TypeError):
        jev_paper_orders=[]
jev_alpaca={'available':bool(jev_paper_status),'status':jev_paper_status,'orders':jev_paper_orders}

paper_risk_comparison_path=A/'PAPER_RISK_REPLAY_COMPARISON_V01.json'
paper_risk_comparison=json.loads(
    paper_risk_comparison_path.read_text(encoding='utf-8')
) if paper_risk_comparison_path.exists() else {
    'version':'v0.1',
    'scenarios':{}
}

paper_control_path=A/'PAPER_TRADING_CONTROL_V01.json'
paper_control=json.loads(paper_control_path.read_text(encoding='utf-8')) if paper_control_path.exists() else {
    'risk_fraction':0.20,
    'allowed_fractions':[0.0,0.2,0.4,0.6,0.8],
    'scope':'PAPER_TRADING_ONLY'
}

def analysis_report(path):
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {'status':'NOT_GENERATED','auto_apply':False}

entry_controls_analysis=analysis_report(A/'ENTRY_CONTROLS_ANALYSIS_V01.json')
jev_calibration_analysis=analysis_report(R.parent/'jev-lab/data/calibration-analysis.json')

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
meta={'entry_controls_analysis':entry_controls_analysis,'jev_calibration_analysis':jev_calibration_analysis,
      'execution_modes':{'JEV_SHADOW':'Simulaciones independientes por snapshot; no cuenta',
       'COMPARATOR_SHADOW':'Hipótesis con reglas comunes; no cuenta',
       'LIVE_PAPER':'Options-System cuenta virtual local; sin órdenes de broker',
       'OPTIONS_ALPACA_PAPER':'Options-System espejo en cuenta Alpaca Paper dedicada',
       'JEV_ALPACA_PAPER':'Jev ejecutor en cuenta Alpaca Paper separada'},
      'discovery_session':'2026-10-02','hypotheses':hypotheses,
      'prospective':evaluation.get('candidates',{}),'prospective_validation':daily,
      'tracker_summary':tracker_summary,'paper_trading':paper_state,
      'options_alpaca_paper':options_alpaca,'jev_alpaca_paper':jev_alpaca,
      'paper_control':paper_control,'paper_risk_comparison':paper_risk_comparison,
      'sizing_simulation':sizing,'stress_testing':stress,'risk_gate':gate,'execution_gate':execution,'readiness':health,'discovery':discovery}
raw=json.dumps(meta,separators=(',',':'))
(A/'research_dashboard_meta.json').write_text(raw,encoding='utf-8')
(A/'research_dashboard_meta.js').write_text('window.RESEARCH_META='+raw+';',encoding='utf-8')
print('RESEARCH_META_OK',len(hypotheses),'prospective_episodes',len(daily.get('prospective_episodes',[])))


publish_meta_views(A/'sessions',meta,refresh_closed=os.getenv('OPTIONS_BUILD_SCOPE')!='today')
