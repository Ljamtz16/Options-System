import json
from pathlib import Path
def test_dashboard_artifacts_exist_and_bind_h03():
 r=Path(__file__).resolve().parents[1]
 a=r/'artifacts/intraday'

 # Discovery evidence remains an explicit immutable seed, not part of every Today payload.
 discovery=json.loads((a/'DISCOVERY_DASHBOARD_2026-10-02.json').read_text(encoding='utf-8'))
 assert len(discovery)==60
 assert sum(bool(x.get('h03')) for x in discovery)==9
 assert all((x.get('symbol') or 'SPY')=='SPY' for x in discovery)

 h=(a/'intraday_research_dashboard.html').read_text(encoding='utf-8')
 loader=(a/'dashboard_loader.js').read_text(encoding='utf-8')
 assert 'Options Research Lab' in h
 assert 'src="dashboard_loader.js"' in h
 assert 'src="intraday_dashboard_data.js"' not in h
 assert 'sessions/index.json' in loader
 assert "sessions/'+day+'.json" in loader
 assert "sessions/'+day+'.meta.json" in loader
 assert "if(historical)Object.assign(meta,await get('sessions/analysis.json'))" in loader

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
 loader=(a/'dashboard_loader.js').read_text(encoding='utf-8')
 assert 'dashboard_loader.js' in html
 assert "loadDashboardScript('research_dashboard_tabs.js')" in html
 assert "get('sessions/'+day+'.meta.json')" in loader
 tabs=(a/'research_dashboard_tabs.js').read_text(encoding='utf-8')
 for label in ('Sesion intradia','Episodios','Hipotesis','Validacion prospectiva','Execution Gate','Discovery Lab'):
  assert label in tabs
 builder=(r/'scripts/build_research_dashboard_meta.py').read_text(encoding='utf-8')
 assert 'publish_meta_views' in builder
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


def test_dashboard_separates_local_and_broker_paper_accounts():
 r=Path(__file__).resolve().parents[1]
 a=r/'artifacts/intraday'
 tabs=(a/'research_dashboard_tabs.js').read_text(encoding='utf-8')
 builder=(r/'scripts/build_research_dashboard_meta.py').read_text(encoding='utf-8')
 for label in ('Options Local','Options Alpaca','Jev Alpaca'):
  assert label in tabs
 for token in ('optionsAlpacaCards','optionsAlpacaTrades','jevAlpacaCards','jevAlpacaOrders'):
  assert token in tabs
 assert "OPTIONS_ALPACA_PAPER_STATE_V01.json" in builder
 assert "data/paper-status.json" in builder
 assert "data/paper.sqlite" in builder
 assert "'options_alpaca_paper':options_alpaca" in builder
 assert "'jev_alpaca_paper':jev_alpaca" in builder


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
