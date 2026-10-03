from options_system.intraday_feature_lab import build_feature_lab

def test_feature_lab_contract_liquidity_and_labels(tmp_path):
 raw=tmp_path/'raw';raw.mkdir()
 chain={'snapshots':{'SPY261005C00100000':{'greeks':{'delta':.5},'latestQuote':{'bp':2,'ap':2.2,'bs':10,'as':12},'impliedVolatility':.2},
                     'SPY261005P00100000':{'greeks':{'delta':-.5},'latestQuote':{'bp':1.8,'ap':2.0,'bs':8,'as':9},'impliedVolatility':.22}}}
 import json
 (raw/'spy_options_x.json').write_text(json.dumps({'captured_at_utc':'2026-10-02T14:00:00+00:00','payload':{'options':{'snapshot':chain}}}))
 state=[{'captured_at_utc':'2026-10-02T14:00:00+00:00','decision_date':'2026-10-02'}]
 out=[{'captured_at_utc':'2026-10-02T14:00:00+00:00','call_mfe_15m':'0.12',
       'call_15m_tp10_sl10':'TP_FIRST','put_mfe_15m':'0.02','put_15m_tp10_sl10':'SL_FIRST'}]
 x=build_feature_lab(state,out,raw)[0]
 assert x['minutes_from_us_open']==30
 assert abs(x['call_spread_pct']-(.2/2.2))<1e-12
 assert x['call_bid_size']==10 and x['call_dte']==3
 assert x['label_call_mfe10_15m']==1 and x['label_put_mfe10_15m']==0
 assert x['label_call_tp10_before_sl10_15m']==1 and x['label_put_tp10_before_sl10_15m']==0

def test_us_open_is_timezone_aware_across_dst(tmp_path):
 raw=tmp_path/'raw';raw.mkdir()
 import json
 chain={'snapshots':{}}
 cases=[('2026-10-02T14:00:00+00:00','2026-10-02'),('2026-11-03T15:00:00+00:00','2026-11-03')]
 state=[];out=[]
 for i,(ts,day) in enumerate(cases):
  (raw/f'spy_options_{i}.json').write_text(json.dumps({'captured_at_utc':ts,'payload':{'options':{'snapshot':chain}}}))
  state.append({'captured_at_utc':ts,'decision_date':day});out.append({'captured_at_utc':ts})
 rows=build_feature_lab(state,out,raw)
 assert [x['minutes_from_us_open'] for x in rows]==[30,30]
