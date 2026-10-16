#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from options_system.options_alpaca_mirror import (
    AlpacaPaperClient,
    MirrorConfig,
    atomic_write_json,
    load_env_file,
    run_mirror,
)

DEFAULT_LOCAL = ROOT / "artifacts/intraday/PAPER_TRADING_LIVE_STATE_V01.json"
DEFAULT_EXTRA_LOCAL = ROOT / "artifacts/intraday/PUT_CONFIRM_LIVE_STATE_V02.json"
DEFAULT_MIRROR = ROOT / "artifacts/intraday/OPTIONS_ALPACA_PAPER_STATE_V01.json"
DEFAULT_LOCK = ROOT / "artifacts/intraday/.options_alpaca_mirror.lock"


class MirrorBusy(RuntimeError):
    pass


@contextmanager
def _single_instance_lock(path: Path = DEFAULT_LOCK, stale_seconds: float = 120.0):
    path.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(2):
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, f"pid={os.getpid()} created={time.time()}\n".encode("utf-8"))
            os.close(fd)
            break
        except FileExistsError:
            try:
                stale = time.time() - path.stat().st_mtime > stale_seconds
            except FileNotFoundError:
                stale = False
            if stale and attempt == 0:
                path.unlink(missing_ok=True)
                continue
            raise MirrorBusy(f"Mirror already running; lock exists: {path}")
    try:
        yield
    finally:
        path.unlink(missing_ok=True)


def _safe_account(a: dict) -> dict:
    keep = (
        "status", "currency", "equity", "cash", "buying_power",
        "pattern_day_trader", "daytrade_count", "options_buying_power",
        "options_approved_level", "options_trading_level",
    )
    return {k: a.get(k) for k in keep if k in a}


def _merge_local_states(states: list[dict]) -> dict:
    open_by_id = {}
    ledger_by_id = {}
    for state in states:
        for row in state.get("live_ledger") or []:
            sid = str(row.get("signal_id") or "")
            if sid:
                ledger_by_id[sid] = dict(row)
        for row in state.get("open_positions") or []:
            sid = str(row.get("signal_id") or "")
            if sid:
                open_by_id[sid] = dict(row)
    for sid in list(open_by_id):
        if sid in ledger_by_id and ledger_by_id[sid].get("status") == "CLOSED":
            open_by_id.pop(sid, None)
    return {
        "mode": "MERGED_LOCAL_PAPER_SOURCES",
        "open_positions": list(open_by_id.values()),
        "live_ledger": list(ledger_by_id.values()),
    }


def _run_enabled(args, cfg: MirrorConfig) -> int:
    cfg.validate(require_start=True)
    local_path = Path(args.local_state).resolve()
    mirror_path = Path(args.mirror_state).resolve()
    if not local_path.exists():
        raise SystemExit(f"Local LIVE PAPER state not found: {local_path}")

    local_paths = [local_path]
    for raw in args.extra_local_state or []:
        p = Path(raw).resolve()
        if p.exists() and p not in local_paths:
            local_paths.append(p)
    local_states = [json.loads(p.read_text(encoding="utf-8")) for p in local_paths]
    local = _merge_local_states(local_states)
    mirror = json.loads(mirror_path.read_text(encoding="utf-8")) if mirror_path.exists() else {"trades": {}}
    mirror["local_sources"] = [str(p) for p in local_paths]

    client = AlpacaPaperClient(cfg.key_id, cfg.secret_key)
    account = client.account()
    positions = client.positions()
    clock = client.clock()
    mirror["account"] = _safe_account(account)
    mirror["broker_positions"] = [
        {k: p.get(k) for k in ("symbol", "qty", "side", "avg_entry_price", "market_value", "unrealized_pl")}
        for p in positions
    ]
    mirror["broker_clock"] = {k: clock.get(k) for k in ("timestamp", "is_open", "next_open", "next_close")}

    mirror, actions = run_mirror(
        local, mirror, cfg, client=client, broker_positions=positions, broker_clock=clock
    )
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


def main() -> int:
    ap = argparse.ArgumentParser(description="Mirror Options-System LIVE PAPER decisions into a dedicated Alpaca Paper account")
    ap.add_argument("--env-file", help="Secret env file; defaults to ~/.config/options-system/options-alpaca-paper.env")
    ap.add_argument("--local-state", default=str(DEFAULT_LOCAL))
    ap.add_argument("--extra-local-state", action="append", default=[])
    ap.add_argument("--no-default-put-confirm", action="store_true")
    ap.add_argument("--lock-file", default=str(DEFAULT_LOCK))
    ap.add_argument("--mirror-state", default=str(DEFAULT_MIRROR))
    ap.add_argument("--check-account", action="store_true", help="Validate dedicated Alpaca Paper credentials only")
    args = ap.parse_args()

    if not args.no_default_put_confirm and str(DEFAULT_EXTRA_LOCAL) not in args.extra_local_state:
        args.extra_local_state.insert(0, str(DEFAULT_EXTRA_LOCAL))
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

    try:
        with _single_instance_lock(Path(args.lock_file)):
            return _run_enabled(args, cfg)
    except MirrorBusy as exc:
        print("OPTIONS_ALPACA_MIRROR_BUSY", str(exc))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
