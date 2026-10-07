import json
from pathlib import Path
def test_dashboard_artifacts_exist_and_bind_h03():
 r=Path(__file__).resolve().parents[1]
 d=json.loads((r/'artifacts/intraday/intraday_dashboard_data.json').read_text(encoding='utf-8'))

 # Frozen discovery session remains intact.
 discovery=[
  x for x in d
  if x.get('decision_date')=='2026-10-02'
  and x.get('session_kind')=='DISCOVERY'
  and x.get('symbol')=='SPY'
 ]
 assert len(discovery)==60
 assert sum(bool(x.get('h03')) for x in discovery)==9

 # Prospective observations coexist with discovery observations.
 prospective=[x for x in d if x.get('session_kind')=='PROSPECTIVE']
 assert prospective

 # H03 is frozen for SPY only.
 assert all(
  not x.get('h03')
  for x in d
  if x.get('symbol')!='SPY'
 )

 h=(r/'artifacts/intraday/intraday_research_dashboard.html').read_text(encoding='utf-8')
 assert 'Options Research Lab' in h
 assert 'research_dashboard_meta.js' in h
 assert 'research_dashboard_tabs.js' in h

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
 for label in ('Sesion intradia','Episodios','Hipotesis','Validacion prospectiva','Execution Gate','Discovery Lab'):
  assert label in tabs
 meta=(a/'research_dashboard_meta.js').read_text(encoding='utf-8')
 for hid in ('CALL_FLOW_REVERSAL_V01','PUT_SKEW_SHORT_V01','H03_CALL_RELATIVE_WEAKNESS_REVERSAL_CANDIDATE','H04_CALL_CROSSMARKET_WEAKNESS_CANDIDATE','H05_PUT_CROSSMARKET_MOMENTUM_CANDIDATE'):
  assert hid in meta

def test_research_tabs_asset_has_no_tool_metadata():
 r=Path(__file__).resolve().parents[1]
 code=(r/'artifacts/intraday/research_dashboard_tabs.js').read_text(encoding='utf-8')
 assert '[Reading ' not in code
 assert '[executed on device:' not in code

def test_research_tab_pages_are_explicitly_shown():
 r=Path(__file__).resolve().parents[1]
 code=(r/'artifacts/intraday/research_dashboard_tabs.js').read_text(encoding='utf-8')
 assert "x.classList.contains('tabpage')?'block':''" in code

def test_all_dashboard_assets_have_no_tool_metadata():
 r=Path(__file__).resolve().parents[1]
 a=r/'artifacts/intraday'
 for p in a.iterdir():
  if p.suffix in {'.html','.js','.json'}:
   code=p.read_text(encoding='utf-8')
   assert '[Reading ' not in code, p.name
   assert '[executed on device:' not in code, p.name

def test_episodes_has_own_tabpage_without_special_click_handler():
 r=Path(__file__).resolve().parents[1]
 code=(r/'artifacts/intraday/research_dashboard_tabs.js').read_text(encoding='utf-8')
 assert "const episodes=make('episodes','')" in code
 assert 'episodes.appendChild(aside)' in code
 assert 'episodes.appendChild(compare)' in code
 assert "querySelector('[data-tab=\"episodes\"]').onclick" not in code


def test_dashboard_exposes_sizing_simulation():
 r=Path(__file__).resolve().parents[1]
 a=r/'artifacts/intraday'
 tabs=(a/'research_dashboard_tabs.js').read_text(encoding='utf-8')
 meta=(a/'research_dashboard_meta.js').read_text(encoding='utf-8')
 assert 'Sizing simulation - not part of frozen hypothesis evidence' in tabs
 assert 'sizing_simulation' in meta
 assert 'execution_and_risk_simulation_only' in meta


def test_dashboard_exposes_execution_gate_tab():
 r=Path(__file__).resolve().parents[1]
 a=r/'artifacts/intraday'
 tabs=(a/'research_dashboard_tabs.js').read_text(encoding='utf-8')
 meta=(a/'research_dashboard_meta.js').read_text(encoding='utf-8')
 assert 'data-tab="exec">Execution Gate' in tabs
 assert "make('exec'" in tabs
 for label in ('Decision por episodio','Politica de ejecucion','Presupuesto','Max contratos','Decision','Motivo'):
  assert label in tabs
 assert 'execution_gate' in meta
 assert 'contract_execution_quality_governance_only' in meta


def test_dashboard_exposes_readiness():
 r=Path(__file__).resolve().parents[1]
 a=r/'artifacts/intraday'
 tabs=(a/'research_dashboard_tabs.js').read_text(encoding='utf-8')
 meta=(a/'research_dashboard_meta.js').read_text(encoding='utf-8')
 assert 'Readiness' in tabs
 assert 'healthchecks' in tabs
 assert 'H03 frozen' in meta
 assert 'readiness' in meta


def test_dashboard_supports_multisession_multisymbol_layer():
 r=Path(__file__).resolve().parents[1]
 a=r/'artifacts/intraday'
 seed=json.loads((a/'DISCOVERY_DASHBOARD_2026-10-02.json').read_text(encoding='utf-8'))
 assert len(seed)==60
 assert {x.get('decision_date') for x in seed}=={'2026-10-02'}
 html=(a/'intraday_research_dashboard.html').read_text(encoding='utf-8')
 assert 'intraday_session_multisymbol.js' in html
 js=(a/'intraday_session_multisymbol.js').read_text(encoding='utf-8')
 for token in ("symbol.id='symbol'",'session_kind','H03 es SPY-only','syncSymbols'):
  assert token in js


def test_dashboard_builder_is_prospective_multisymbol_compatible():
 r=Path(__file__).resolve().parents[1]
 code=(r/'scripts/build_intraday_dashboard_data.py').read_text(encoding='utf-8')
 assert 'intraday_options_v2.csv' in code
 assert 'DISCOVERY_DASHBOARD_2026-10-02.json' in code
 assert 'symbol_from_open' in code
 assert 'if row.get("symbol") != "SPY"' in code
 assert 'session_kind' in code


def test_dashboard_publishers_rebuild_and_publish_multisymbol_asset():
 r=Path(__file__).resolve().parents[1]
 for name in ('vps_postclose.py','publish_intraday_dashboard_live.py'):
  code=(r/'scripts'/name).read_text(encoding='utf-8')
  assert 'scripts/build_intraday_dashboard_data.py' in code
  assert 'intraday_session_multisymbol.js' in code
