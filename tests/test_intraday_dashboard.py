import json
from pathlib import Path
def test_dashboard_artifacts_exist_and_bind_h03():
 r=Path(__file__).resolve().parents[1]
 d=json.loads((r/'artifacts/intraday/intraday_dashboard_data.json').read_text(encoding='utf-8'))
 assert len(d)==60
 assert sum(bool(x['h03']) for x in d)==9
 h=(r/'artifacts/intraday/intraday_research_dashboard.html').read_text(encoding='utf-8')
 assert 'Options Research Lab' in h and 'H03 episodes' in h and 'EXPLORATORY_ONLY' in h

def test_episode_comparator_asset_is_loadable():
 r=Path(__file__).resolve().parents[1]
 html=r/'artifacts/intraday/intraday_research_dashboard.html'
 h=html.read_text(encoding='utf-8')
 assert 'src="intraday_episode_compare.js"' in h
 js=html.parent/'intraday_episode_compare.js'
 assert js.exists()
 code=js.read_text(encoding='utf-8')
 assert 'toggleEpisodeCompare' in code
 assert 'refreshEpisodeComparison' in code
 assert 'EP_COMPARE_SELECTED' in code

def test_research_dashboard_tabs_and_meta_exist():
 r=Path(__file__).resolve().parents[1]
 a=r/'artifacts/intraday'
 html=(a/'intraday_research_dashboard.html').read_text(encoding='utf-8')
 assert 'research_dashboard_meta.js' in html
 assert 'research_dashboard_tabs.js' in html
 tabs=(a/'research_dashboard_tabs.js').read_text(encoding='utf-8')
 for label in ('Sesión intradía','Episodios','Hipótesis','Validación prospectiva','Discovery Lab'):
  assert label in tabs
 meta=(a/'research_dashboard_meta.js').read_text(encoding='utf-8')
 for hid in ('CALL_FLOW_REVERSAL_V01','PUT_SKEW_SHORT_V01','H03_CALL_RELATIVE_WEAKNESS_REVERSAL_CANDIDATE','H04_CALL_CROSSMARKET_WEAKNESS_CANDIDATE','H05_PUT_CROSSMARKET_MOMENTUM_CANDIDATE'):
  assert hid in meta
