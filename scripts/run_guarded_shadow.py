import csv
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from options_system.guarded_shadow import build_guarded_shadow

A = ROOT / "artifacts" / "intraday"
STATE = A / "PAPER_TRADING_LIVE_STATE_V01.json"
TRACKER = ROOT / "data/processed/intraday/prospective_hypothesis_tracker_v02.csv"
CONFIG = ROOT / "config/guarded_shadow_v01.json"
OUT = A / "GUARDED_SHADOW_V01.json"

if not STATE.exists():
    raise SystemExit("GUARDED_SHADOW_NO_LIVE_STATE")
state = json.loads(STATE.read_text(encoding="utf-8"))
config = json.loads(CONFIG.read_text(encoding="utf-8")) if CONFIG.exists() else {}
rows = list(csv.DictReader(TRACKER.open(encoding="utf-8"))) if TRACKER.exists() else []
report = build_guarded_shadow(state, rows, config, datetime.now(timezone.utc))
tmp = OUT.with_suffix(".tmp")
tmp.write_text(json.dumps(report, indent=2), encoding="utf-8")
tmp.replace(OUT)

today = max(report["by_day"], default=None)
t = report["by_day"].get(today, {}) if today else {}
print("GUARDED_SHADOW_OK", f"day={today}", f"frozen={t.get('frozen_trades',0)}",
      f"guarded={t.get('guarded_trades',0)}", f"skipped={t.get('skipped_trades',0)}",
      f"frozen_pnl={t.get('frozen_net_pnl',0):.2f}", f"guarded_pnl={t.get('guarded_net_pnl',0):.2f}",
      f"halts={t.get('halts',0)}", f"rearms={t.get('rearms',0)}")
