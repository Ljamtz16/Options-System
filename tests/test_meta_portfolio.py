from datetime import datetime,timezone
from options_system.meta_portfolio import score
from options_system.meta_portfolio_live import init_state,select_contract

def cand(source='MULTI',support=1,spread=.02,premium=2.0,corr=0):
 return {'source':source,'symbol':'SPY','side':'PUT','meta':{'support_count':support,'market_regime':'RISK_OFF','spread_pct':spread,'entry_ask':premium,'correlation_exposure':corr}}

def test_ranking_prefers_h09_and_single_support():
 assert score(cand(source='H09')) > score(cand(source='MULTI'))
 assert score(cand(support=1)) > score(cand(support=2))

def test_live_state_starts_flat_at_1000():
 s=init_state(datetime(2026,10,16,tzinfo=timezone.utc),event_lines=10,last_snapshot_file='x.json')
 assert s['cash']==1000 and s['equity']==1000 and not s['open_positions']
 assert s['episode_event_line']==10 and s['last_snapshot_file']=='x.json'

def test_selector_uses_buying_power_and_delta_without_fixed_premium_cap():
 snap={'payload':{'symbols':{'SPY':{'option_snapshot':{'snapshots':{
  'SPY261019P00760000':{'latestQuote':{'bp':2.9,'ap':3.0,'bs':2,'as':2},'greeks':{'delta':-.50},'dailyBar':{'v':100}},
  'SPY261019P00750000':{'latestQuote':{'bp':8.8,'ap':9.0,'bs':2,'as':2},'greeks':{'delta':-.49},'dailyBar':{'v':100}},
 }}}}}}
 now=datetime(2026,10,16,14,0,tzinfo=timezone.utc)
 x=select_contract(snap,'SPY','PUT',1000,now)
 assert x and x['contract']=='SPY261019P00760000'
 assert select_contract(snap,'SPY','PUT',250,now) is None
