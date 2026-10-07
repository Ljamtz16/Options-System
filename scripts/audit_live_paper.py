#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from options_system.live_paper_audit import audit, render_text


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit Options-System local LIVE PAPER ledger for one session date")
    ap.add_argument("--date", required=True, help="Session date YYYY-MM-DD")
    ap.add_argument("--state", default="artifacts/intraday/PAPER_TRADING_LIVE_STATE_V01.json")
    ap.add_argument("--out-dir", default="artifacts/intraday/live_paper_audits")
    ap.add_argument("--stdout-only", action="store_true", help="Do not write report files")
    args = ap.parse_args()

    state_path = Path(args.state)
    if not state_path.exists():
        raise SystemExit(f"State file not found: {state_path}")

    state = json.loads(state_path.read_text(encoding="utf-8"))
    result = audit(state, args.date)
    text = render_text(result)
    print(text)

    if not args.stdout_only:
        out = Path(args.out_dir)
        out.mkdir(parents=True, exist_ok=True)
        stem = f"LIVE_PAPER_AUDIT_{args.date}"
        json_path = out / f"{stem}.json"
        text_path = out / f"{stem}.txt"
        json_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        text_path.write_text(text, encoding="utf-8")
        print(f"JSON: {json_path.resolve()}")
        print(f"TEXT: {text_path.resolve()}")

    return 1 if result.get("status") == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
