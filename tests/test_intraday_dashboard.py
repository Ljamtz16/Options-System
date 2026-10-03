import json
from pathlib import Path
def test_dashboard_artifacts_exist_and_bind_h03():
 r=Path(__file__).resolve().parents[1]
 d=json.loads((r/'artifacts/intraday/intraday_dashboard_data.json').read_text(encoding='utf-8'))
 assert len(d)==60
 assert sum(bool(x['h03']) for x in d)==9
 h=(r/'artifacts/intraday/intraday_research_dashboard.html').read_text(encoding='utf-8')
 assert 'Options Research Lab' in h and 'H03 episodes' in h and 'EXPLORATORY_ONLY' in h
