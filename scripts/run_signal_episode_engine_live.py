#!/usr/bin/env python3
from __future__ import annotations

import fcntl
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from options_system.session_cache import atomic_text
from options_system.signal_episode_engine import apply_activation, apply_meta_decision

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts/intraday"
CFG_PATH = ROOT / "config/signal_episode_engine_v01.json"
STATE_PATH = ART / "SIGNAL_EPISODE_LIVE_STATE_V01.json"
EVENTS_PATH = ART / "SIGNAL_EPISODE_LIVE_EVENTS_V01.jsonl"
LOCK_PATH = ART / ".signal_episode_live_v01.lock"
SOURCES = {
    "meta": ART / "META_DECISION_LIVE_EVENTS_V01.jsonl",
    "h01": ART / "FROZEN_HYPOTHESES_LIVE_EVENTS_V01.jsonl",
    "h09": ART / "H09_PUT_FLOW_LIVE_EVENTS_V01.jsonl",
    "multi": ART / "MULTISYMBOL_LIVE_EVENTS_V01.jsonl",
}
LOOP_SECONDS = 5


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def offsets_at_eof() -> dict[str, int]:
    return {name: path.stat().st_size if path.exists() else 0 for name, path in SOURCES.items()}


def initial_state(cfg: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": cfg["version"],
        "mode": cfg["mode"],
        "auto_apply": False,
        "broker_orders_enabled": False,
        "live_start_utc": now_iso(),
        "source_offsets": offsets_at_eof(),
        "active_episodes": {},
        "recent_episodes": [],
        "episode_sequences": {},
        "direction_memory": {},
        "counters": {
            "observations": 0,
            "activations": 0,
            "meta_decisions": 0,
            "ttt_confirmations": 0,
            "would_authorize": 0,
            "by_source": {},
        },
        "updated_at_utc": now_iso(),
    }


def save(state: dict[str, Any]) -> None:
    state["updated_at_utc"] = now_iso()
    atomic_text(STATE_PATH, json.dumps(state, indent=2) + "\n")


def log_event(payload: dict[str, Any]) -> None:
    EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with EVENTS_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"logged_at_utc": now_iso(), **payload}, sort_keys=True) + "\n")


def load_state(cfg: dict[str, Any]) -> dict[str, Any]:
    if not STATE_PATH.exists():
        state = initial_state(cfg)
        save(state)
        log_event({"event": "SIGNAL_EPISODE_BASELINE", "source_offsets": state["source_offsets"]})
        return state
    state = load_json(STATE_PATH, {})
    if state.get("version") != cfg.get("version"):
        raise RuntimeError("SIGNAL_EPISODE_POLICY_VERSION_MISMATCH_FAIL_CLOSED")
    return state


def read_new(path: Path, offset: int) -> tuple[list[dict[str, Any]], int]:
    if not path.exists():
        return [], offset
    size = path.stat().st_size
    if size < offset:
        raise RuntimeError(f"SIGNAL_EPISODE_SOURCE_TRUNCATED:{path.name}")
    out: list[dict[str, Any]] = []
    with path.open("rb") as handle:
        handle.seek(offset)
        while True:
            raw = handle.readline()
            if not raw:
                break
            offset = handle.tell()
            if not raw.strip():
                continue
            try:
                out.append(json.loads(raw.decode("utf-8")))
            except ValueError:
                continue
    return out, offset


def normalize_activation(source_name: str, event: dict[str, Any]) -> dict[str, Any] | None:
    kind = event.get("event")
    if source_name == "h01" and kind == "SIGNAL" and event.get("hypothesis") == "CALL_FLOW_REVERSAL_V01":
        return {
            "kind": "activation", "source": "H01", "symbol": "SPY", "side": "CALL",
            "candidate_id": event.get("hypothesis"), "signal_time": event.get("signal_time") or event.get("logged_at_utc"),
            "logged_at_utc": event.get("logged_at_utc"),
        }
    if source_name == "h09" and kind == "H09_ACTIVATION":
        return {
            "kind": "activation", "source": "H09", "symbol": "SPY", "side": "PUT",
            "candidate_id": event.get("candidate_id"), "signal_time": event.get("signal_time"),
            "logged_at_utc": event.get("logged_at_utc"),
        }
    if source_name == "multi" and kind == "MULTISYMBOL_ACTIVATION":
        return {
            "kind": "activation", "source": "MULTI", "symbol": event.get("symbol"), "side": str(event.get("side") or "").upper(),
            "candidate_id": event.get("candidate_id"), "signal_time": event.get("signal_time"),
            "logged_at_utc": event.get("logged_at_utc"),
        }
    return None


def normalize_meta(event: dict[str, Any]) -> dict[str, Any] | None:
    if event.get("event") != "META_DECISION":
        return None
    row = dict(event)
    row.pop("event", None)
    row["kind"] = "meta"
    return row


def event_order(row: dict[str, Any]) -> tuple[str, int]:
    stamp = str(row.get("logged_at_utc") or row.get("signal_time") or row.get("time") or "")
    return stamp, 0 if row.get("kind") == "activation" else 1


def bump_source(state: dict[str, Any], source: str, field: str) -> None:
    bucket = state["counters"]["by_source"].setdefault(source, {"activations": 0, "meta_decisions": 0, "ttt_confirmations": 0})
    bucket[field] = int(bucket.get(field) or 0) + 1


def process_observation(state: dict[str, Any], cfg: dict[str, Any], row: dict[str, Any]) -> None:
    state["counters"]["observations"] += 1
    if row["kind"] == "activation":
        ep = apply_activation(state, row, cfg)
        state["counters"]["activations"] += 1
        bump_source(state, ep["source"], "activations")
        event_name = "EPISODE_ACTIVATION"
    else:
        ep = apply_meta_decision(state, row, cfg)
        state["counters"]["meta_decisions"] += 1
        bump_source(state, ep["source"], "meta_decisions")
        event_name = "EPISODE_META_DECISION"
    if ep.get("would_authorize_new_trade"):
        state["counters"]["ttt_confirmations"] += 1
        state["counters"]["would_authorize"] += 1
        bump_source(state, ep["source"], "ttt_confirmations")
        log_event({
            "event": "TTT_CONFIRMED", "episode_id": ep["episode_id"], "source": ep["source"], "symbol": ep["symbol"],
            "side": ep["side"], "ttt_state": ep["ttt_state"], "shadow_decision": ep["shadow_decision"],
            "activation_count": len(ep.get("activation_times") or []), "meta_decision": ep.get("latest_meta_decision"),
            "broker_order": False, "auto_apply": False,
        })
    log_event({
        "event": event_name, "episode_id": ep["episode_id"], "source": ep["source"], "symbol": ep["symbol"], "side": ep["side"],
        "ttt_state": ep["ttt_state"], "hysteresis_state": ep["hysteresis_state"], "shadow_decision": ep["shadow_decision"],
        "activation_count": len(ep.get("activation_times") or []), "meta_decision": ep.get("latest_meta_decision"),
        "would_authorize_new_trade": bool(ep.get("would_authorize_new_trade")), "broker_order": False,
    })


def tick(state: dict[str, Any], cfg: dict[str, Any]) -> int:
    batch: list[dict[str, Any]] = []
    for name, path in SOURCES.items():
        rows, offset = read_new(path, int(state["source_offsets"].get(name, 0)))
        state["source_offsets"][name] = offset
        for event in rows:
            row = normalize_meta(event) if name == "meta" else normalize_activation(name, event)
            if row and row.get("source") and row.get("symbol") and row.get("side"):
                batch.append(row)
    batch.sort(key=event_order)
    for row in batch:
        process_observation(state, cfg, row)
    save(state)
    return len(batch)


def main() -> None:
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOCK_PATH.open("a+") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        cfg = load_json(CFG_PATH, {})
        state = load_state(cfg)
        print(f"SIGNAL_EPISODE_LIVE_STARTED offsets={state['source_offsets']} mode={state['mode']}", flush=True)
        while True:
            count = tick(state, cfg)
            if count:
                print(f"SIGNAL_EPISODE_LIVE_OK new={count} counters={state['counters']}", flush=True)
            time.sleep(LOOP_SECONDS)


if __name__ == "__main__":
    main()
