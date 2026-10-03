import csv,json
from pathlib import Path
from options_system.intraday_episodes import summarize_episodes
from options_system.option_costs import daily_regulatory_fees
R=Path(__file__).resolve().parents[1]
rows=list(csv.DictReader(open(R/'data/processed/intraday/intraday_feature_lab_v01.csv',encoding='utf-8')))
for r in rows:
    try:r['h03']=float(r.get('iwm_from_open',''))<=-0.003338055604745982 and float(r.get('spy_from_open',''))<=-0.002140966419266088
    except (TypeError,ValueError):r['h03']=False
eps=summarize_episodes(rows,'h03','call',60,6)
dec=[e for e in eps if e['tp_before_sl'] is not None]
report={'version':'v0.1','status':'EXPLORATORY_ONLY','candidate':'H03_CALL_RELATIVE_WEAKNESS_REVERSAL_CANDIDATE',
        'episode_definition':'consecutive activations separated by no more than 6 minutes; first activation is episode entry',
        'episodes':eps,'summary':{'n_episodes':len(eps),'tp_sl_decided':len(dec),
        'tp_first':sum(e['tp_before_sl'] for e in dec),'tp_before_sl_rate':sum(e['tp_before_sl'] for e in dec)/len(dec) if dec else None}}
trades=[e['trade_1_contract'] for e in eps if e.get('trade_1_contract')]
fees=daily_regulatory_fees(trades)
gross=sum(t['gross_pnl'] for t in trades)
report['money_1_contract']={'trades':len(trades),'gross_pnl':gross,'daily_regulatory_fees':fees,'net_observed':gross-fees['total'],'net_with_1c_extra_slippage_per_leg':gross-fees['total']-2*len(trades),'net_with_2c_extra_slippage_per_leg':gross-fees['total']-4*len(trades),'spread_handling':'already included: buy at ask, exit path at bid'}
out=R/'artifacts/intraday/H03_EPISODE_ANALYSIS_V01.json';out.write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report['summary']))
