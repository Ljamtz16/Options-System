from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[1]
A=ROOT/'artifacts'/'intraday'
WEB=Path('/var/www/options-dashboard')
html=WEB/'intraday_research_dashboard.html'
js=A/'dashboard_dynamic_live.js'
if not WEB.is_dir() or not html.exists():
    raise SystemExit(f'DASHBOARD_NOT_FOUND {WEB}')
shutil.copy2(js,WEB/js.name)
s=html.read_text(encoding='utf-8')
tag='<script src="dashboard_dynamic_live.js"></script>'
if tag not in s:
    s=s.replace('</body>',tag+'</body>')
    html.write_text(s,encoding='utf-8')
print('DYNAMIC_DASHBOARD_PATCH_DEPLOYED',WEB)
