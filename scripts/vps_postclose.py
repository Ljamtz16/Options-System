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
)

for task in TASKS:
    p=ROOT/task
    if not p.exists():
        print(f"SKIP_MISSING {task}")
        continue
    print(f"RUN {task}")
    subprocess.run([PY,str(p)],cwd=ROOT,check=True)
print("POSTCLOSE_OK")
