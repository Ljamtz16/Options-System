import subprocess,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PY=sys.executable

TASKS=(
    "scripts/build_prospective_market_state.py",
    "scripts/label_prospective_market_state.py",
    "scripts/market_state_readiness.py",
    "scripts/build_intraday_dataset.py",
    "scripts/build_intraday_scoreboard.py",
    "scripts/intraday_daily_report.py",
    "scripts/build_spy_intraday_outcomes_all_days.py",
    "scripts/track_frozen_hypotheses.py",
    "scripts/hypothesis_daily_report.py",
    "scripts/build_prospective_sizing_comparison.py",
    "scripts/build_prospective_stress_test.py",
    "scripts/build_prospective_risk_gate.py",
    "scripts/build_prospective_execution_gate.py",
    "scripts/build_prospective_governance.py",
    "scripts/build_research_dashboard_meta.py",
)

OPTIONAL_INPUTS={
    "scripts/build_intraday_scoreboard.py": ROOT/"data/processed/intraday/intraday_options_v2.csv",
    "scripts/intraday_daily_report.py": ROOT/"data/processed/intraday/intraday_options_v2.csv",
}

for task in TASKS:
    p=ROOT/task
    if not p.exists():
        print(f"SKIP_MISSING {task}")
        continue
    required=OPTIONAL_INPUTS.get(task)
    if required is not None and not required.exists():
        print(f"SKIP_NO_INPUT {task} input={required.relative_to(ROOT)}")
        continue
    print(f"RUN {task}")
    subprocess.run([PY,str(p)],cwd=ROOT,check=True)
# Publish the refreshed static dashboard when a web directory is available.
WEB_DIR = Path("/var/www/options-dashboard")
DASHBOARD_FILES = (
    "intraday_research_dashboard.html",
    "intraday_dashboard_data.js",
    "research_dashboard_meta.js",
    "intraday_episode_compare.js",
    "research_dashboard_tabs.js",
)

if WEB_DIR.is_dir():
    for name in DASHBOARD_FILES:
        src = ROOT / "artifacts/intraday" / name
        if not src.exists():
            raise FileNotFoundError(f"Dashboard asset missing: {src}")
        (WEB_DIR / name).write_bytes(src.read_bytes())
    print(f"DASHBOARD_PUBLISHED {WEB_DIR}")
else:
    print(f"SKIP_DASHBOARD_PUBLISH missing={WEB_DIR}")

print("POSTCLOSE_OK")
