#!/usr/bin/env python3
"""Read existing tracker, emit isolated PUT research artifacts; never place orders."""
import argparse
import csv
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from options_system.put_research_shadow import analyze
from audit_put_baseline import audit_h02


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tracker", default=str(ROOT / "data/processed/intraday/prospective_hypothesis_tracker_v02.csv"))
    parser.add_argument("--config", default=str(ROOT / "config/put_research_shadow_v01.json"))
    parser.add_argument("--output", default=str(ROOT / "artifacts/intraday/PUT_RESEARCH_SHADOW_V01.json"))
    args = parser.parse_args()
    with open(args.tracker, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
    report = analyze(rows, cfg)
    report["h02_frozen_baseline_audit"] = audit_h02(rows)
    report["created_after_sessions"] = "2026-10-13"
    report["validation_policy"] = "All sessions through 2026-10-13 are historical diagnostics, never prospective evidence for H06/H07/H08."
    dest = Path(args.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    temp = dest.with_suffix(dest.suffix + ".tmp")
    temp.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    os.replace(temp, dest)
    print(json.dumps({"mode": report["mode"], "sessions": len(report["sessions"]), "rows": report["rows"],
                      "summary": {k: {"episodes": v["episodes"], "mean_put_return_15m": v["mean_put_return_15m"]}
                                  for k, v in report["summary"].items()}}, indent=2))


if __name__ == "__main__":
    main()
