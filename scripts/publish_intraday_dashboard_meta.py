import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable

WEB_DIR = Path("/var/www/options-dashboard")
META_JS = ROOT / "artifacts/intraday/research_dashboard_meta.js"

subprocess.run(
    [PYTHON, str(ROOT / "scripts/build_research_dashboard_meta.py")],
    cwd=ROOT,
    check=True,
)

if not WEB_DIR.is_dir():
    raise SystemExit(f"WEB_DIR_MISSING {WEB_DIR}")

if not META_JS.exists():
    raise SystemExit(f"META_JS_MISSING {META_JS}")

(WEB_DIR / "research_dashboard_meta.js").write_bytes(META_JS.read_bytes())

print(f"INTRADAY_DASHBOARD_META_PUBLISHED {WEB_DIR / 'research_dashboard_meta.js'}")
