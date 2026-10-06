import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
WEB_DIR = Path("/var/www/options-dashboard")
A = ROOT / "artifacts" / "intraday"

TASKS = [
    "scripts/build_prospective_market_state.py",
    "scripts/label_prospective_market_state.py",
    "scripts/market_state_readiness.py",
    "scripts/build_intraday_dataset.py",
    "scripts/build_intraday_scoreboard.py",
    "scripts/build_intraday_dashboard_data.py",
    "scripts/intraday_daily_report.py",
    "scripts/build_spy_intraday_outcomes_all_days.py",
    "scripts/track_frozen_hypotheses.py",
    "scripts/hypothesis_daily_report.py",
    "scripts/build_prospective_sizing_comparison.py",
    "scripts/build_prospective_stress_test.py",
    "scripts/build_prospective_risk_gate.py",
    "scripts/build_prospective_execution_gate.py",
    "scripts/build_research_dashboard_meta.py",
]

PUBLISH = [
    "intraday_research_dashboard.html",
    "intraday_dashboard_data.js",
    "intraday_session_multisymbol.js",
    "research_dashboard_meta.js",
    "intraday_episode_compare.js",
    "research_dashboard_tabs.js",
]

for task in TASKS:
    print(f"RUN {task}", flush=True)
    subprocess.run([PYTHON, str(ROOT / task)], cwd=ROOT, check=True)

if not WEB_DIR.is_dir():
    raise SystemExit(f"WEB_DIR_MISSING {WEB_DIR}")

for name in PUBLISH:
    src = A / name
    if src.exists():
        shutil.copy2(src, WEB_DIR / name)
        print(f"PUBLISHED {name}", flush=True)
    else:
        print(f"SKIP_MISSING {name}", flush=True)

print(f"INTRADAY_DASHBOARD_LIVE_PUBLISHED {WEB_DIR}", flush=True)
