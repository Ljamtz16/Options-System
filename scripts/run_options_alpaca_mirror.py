#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from options_system.options_alpaca_mirror import (
    AlpacaPaperClient,
    MirrorConfig,
    atomic_write_json,
    load_env_file,
    run_mirror,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOCAL = ROOT / "artifacts/intraday/PAPER_TRADING_LIVE_STATE_V01.json"
DEFAULT_MIRROR = ROOT / "artifacts/intraday/OPTIONS_ALPACA_PAPER_STATE_V01.json"


def _safe_account(a: dict) -> dict:
    keep = (
        "status", "currency", "equity", "cash", "buying_power",
        "pattern_day_trader", "daytrade_count", "options_buying_power",
        "options_approved_level", "options_trading_level",
    )
    return {k: a.get(k) for k in keep if k in a}


def main() -> int:
    ap = argparse.ArgumentParser(description="Mirror Options-System LIVE PAPER decisions into a dedicated Alpaca Paper account")
    ap.add_argument("--env-file", help="Secret env file; defaults to ~/.config/options-system/options-alpaca-paper.env")
    ap.add_argument("--local-state", default=str(DEFAULT_LOCAL))
    ap.add_argument("--mirror-state", default=str(DEFAULT_MIRROR))
    ap.add_argument("--check-account", action="store_true", help="Validate dedicated Alpaca Paper credentials only")
    args = ap.parse_args()

    env_path = load_env_file(args.env_file)
    cfg = MirrorConfig.from_env()

    if args.check_account:
        cfg.validate(require_start=False)
        account = AlpacaPaperClient(cfg.key_id, cfg.secret_key).account()
        print("OPTIONS_ALPACA_ACCOUNT_OK")
        print(json.dumps(_safe_account(account), indent=2))
        if env_path:
            print(f"ENV_FILE {env_path}")
        return 0

    if not cfg.enabled:
        print("OPTIONS_ALPACA_MIRROR_DISABLED")
        return 0

    cfg.validate(require_start=True)
    local_path = Path(args.local_state)
    mirror_path = Path(args.mirror_state)
    if not local_path.exists():
        raise SystemExit(f"Local LIVE PAPER state not found: {local_path}")

    local = json.loads(local_path.read_text(encoding="utf-8"))
    mirror = json.loads(mirror_path.read_text(encoding="utf-8")) if mirror_path.exists() else {"trades": {}}

    client = AlpacaPaperClient(cfg.key_id, cfg.secret_key)
    account = client.account()
    mirror["account"] = _safe_account(account)

    mirror, actions = run_mirror(local, mirror, cfg, client=client)
    mirror["last_actions"] = actions
    atomic_write_json(mirror_path, mirror)

    counts = {}
    for t in (mirror.get("trades") or {}).values():
        counts[t.get("status", "UNKNOWN")] = counts.get(t.get("status", "UNKNOWN"), 0) + 1

    print(
        "OPTIONS_ALPACA_MIRROR_OK",
        f"submit_orders={cfg.submit_orders}",
        f"actions={len(actions)}",
        f"tracked={len(mirror.get('trades') or {})}",
        f"states={json.dumps(counts, sort_keys=True)}",
    )
    for action in actions:
        print("ACTION", json.dumps(action, sort_keys=True))
    print(f"STATE {mirror_path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
