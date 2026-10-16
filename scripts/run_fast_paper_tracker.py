import json
import time
from datetime import datetime, timezone
from pathlib import Path

from options_system.prospective_collector import option_latest_quotes
from options_system.snapshot_store import write_immutable_snapshot, append_index

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / "artifacts" / "intraday"

STATE = A / "PAPER_TRADING_LIVE_STATE_V01.json"

OUT_DIR = ROOT / "data" / "raw" / "paper_fast"
INDEX = OUT_DIR / "index.jsonl"

INTERVAL_SECONDS = 15
FEED = "indicative"


def utcnow():
    return datetime.now(timezone.utc)


def load_state():
    if not STATE.exists():
        return None

    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except Exception:
        return None


def active_contracts(state):
    positions = state.get("open_positions") or []

    return sorted({
        p.get("contract")
        for p in positions
        if p.get("contract")
    })


def normalize_quote(raw, contract):
    quotes = raw.get("quotes") or {}
    q = quotes.get(contract)

    if not q:
        return None

    return {
        "contract": contract,
        "bid": q.get("bp"),
        "ask": q.get("ap"),
        "bid_size": q.get("bs"),
        "ask_size": q.get("as"),
        "quote_time": q.get("t"),
    }


def capture_once():
    state = load_state()

    if not state:
        print("FAST_TRACKER_NO_STATE", flush=True)
        return

    contracts = active_contracts(state)

    if not contracts:
        print("FAST_TRACKER_IDLE no_open_positions", flush=True)
        return

    raw = option_latest_quotes(contracts, feed=FEED)

    quotes = {}

    for contract in contracts:
        q = normalize_quote(raw, contract)
        if q:
            quotes[contract] = q

    positions = []

    for pos in state.get("open_positions") or []:
        contract = pos.get("contract")
        q = quotes.get(contract)

        record = {
            "signal_id": pos.get("signal_id"),
            "contract": contract,
            "entry_ask": pos.get("entry_ask"),
            "entry_time": pos.get("entry_time"),
            "quantity": pos.get("quantity"),
            "quote": q,
        }

        if q and q.get("bid") not in (None, ""):
            entry = float(pos["entry_ask"])
            bid = float(q["bid"])

            ret = (bid - entry) / entry

            record["return_from_entry"] = ret

            if ret >= 0.10:
                record["threshold_state"] = "TP10"
            elif ret <= -0.10:
                record["threshold_state"] = "SL10"
            else:
                record["threshold_state"] = "OPEN"

        positions.append(record)

    payload = {
        "schema_version": "paper_fast_v1",
        "collector_protocol": {
            "version": "v2",
            "target_interval_seconds": INTERVAL_SECONDS,
            "feed": FEED,
            "scope": "OPEN_PAPER_POSITIONS_ONLY",
        },
        "positions": positions,
    }

    path, digest = write_immutable_snapshot(
        payload,
        OUT_DIR,
        "paper_fast",
    )

    append_index(path, digest, INDEX)

    print(
        "FAST_TRACKER_SAVED",
        f"contracts={len(contracts)}",
        f"quotes={len(quotes)}",
        f"path={path.name}",
        flush=True,
    )


def main():
    print(
        "FAST_TRACKER_START",
        f"interval={INTERVAL_SECONDS}s",
        f"feed={FEED}",
        flush=True,
    )

    while True:
        started = time.monotonic()

        try:
            capture_once()
        except Exception as exc:
            print(
                "FAST_TRACKER_ERROR",
                f"{type(exc).__name__}: {exc}",
                flush=True,
            )

        elapsed = time.monotonic() - started
        sleep_for = max(1.0, INTERVAL_SECONDS - elapsed)

        time.sleep(sleep_for)


if __name__ == "__main__":
    main()
