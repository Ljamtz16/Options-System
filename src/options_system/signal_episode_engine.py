from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any


def parse_dt(value: Any) -> datetime:
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def source_key(source: str, symbol: str) -> str:
    return f"{source}:{symbol}"


def episode_slot(source: str, symbol: str, side: str) -> str:
    return f"{source}:{symbol}:{side}"


def observation_time(row: dict[str, Any]) -> str:
    return str(row.get("signal_time") or row.get("time") or row.get("logged_at_utc") or "")


def new_episode(source: str, symbol: str, side: str, stamp: str, seq: int) -> dict[str, Any]:
    return {
        "episode_id": f"{source}:{symbol}:{stamp[:10]}:E{seq}",
        "source": source,
        "symbol": symbol,
        "side": side,
        "started_at": stamp,
        "last_observation_at": stamp,
        "activation_times": [],
        "candidate_ids": [],
        "meta_decision_count": 0,
        "latest_meta_decision": None,
        "latest_meta_id": None,
        "latest_block_reasons": [],
        "latest_wait_reasons": [],
        "flip_count_30m": 0,
        "ttt_state": "BUILDING",
        "hysteresis_state": "NEUTRAL",
        "shadow_decision": "WAIT",
        "confirmed_at": None,
        "confirmation_memory_until": None,
        "would_authorize_new_trade": False,
        "authorization_emitted": False,
        "updated_at": stamp,
    }


def should_start_new(ep: dict[str, Any] | None, stamp: str, side: str, gap_minutes: int) -> bool:
    if not ep:
        return True
    if ep.get("side") != side:
        return True
    return (parse_dt(stamp) - parse_dt(ep["last_observation_at"])).total_seconds() > gap_minutes * 60


def recent_activation_count(ep: dict[str, Any], stamp: str, window_minutes: int) -> int:
    now = parse_dt(stamp)
    return sum((now - parse_dt(t)).total_seconds() <= window_minutes * 60 for t in ep.get("activation_times") or [])


def update_flip_memory(state: dict[str, Any], source: str, symbol: str, side: str, stamp: str, flicker_minutes: int) -> int:
    key = source_key(source, symbol)
    prev = (state.setdefault("direction_memory", {})).get(key)
    flips = 0
    if prev:
        delta = (parse_dt(stamp) - parse_dt(prev["time"])).total_seconds()
        if 0 <= delta <= flicker_minutes * 60 and prev.get("side") != side:
            flips = int(prev.get("flips") or 0) + 1
        elif 0 <= delta <= flicker_minutes * 60:
            flips = int(prev.get("flips") or 0)
    state["direction_memory"][key] = {"time": stamp, "side": side, "flips": flips}
    return flips


def recompute_episode(ep: dict[str, Any], cfg: dict[str, Any], stamp: str) -> tuple[str, bool]:
    source = ep["source"]
    policy = (cfg.get("ttt") or {}).get(source, {})
    mode = policy.get("mode", "ACTIVATION_2_OF_3")
    meta = ep.get("latest_meta_decision")
    prior = ep.get("shadow_decision")
    authorize = False

    if meta == "BLOCK":
        ep["ttt_state"] = "META_BLOCK"
        ep["hysteresis_state"] = "RESET_BY_BLOCK"
        ep["shadow_decision"] = "BLOCK"
        return ep["shadow_decision"], False

    if meta == "WAIT":
        ep["ttt_state"] = "META_WAIT"
        if ep.get("confirmed_at") and ep.get("confirmation_memory_until") and parse_dt(stamp) <= parse_dt(ep["confirmation_memory_until"]):
            ep["hysteresis_state"] = "CONFIRMATION_MEMORY"
        else:
            ep["hysteresis_state"] = "NEUTRAL"
        ep["shadow_decision"] = "WAIT"
        return ep["shadow_decision"], False

    if meta != "ACCEPT":
        ep["ttt_state"] = "WAIT_META_DECISION"
        ep["shadow_decision"] = "WAIT"
        return ep["shadow_decision"], False

    if mode == "FIRST_CLEAN_META":
        confirmed = ep.get("meta_decision_count", 0) >= 1 and ep.get("flip_count_30m", 0) <= int(policy.get("max_flips", 0))
        ep["ttt_state"] = "CONFIRMED_FIRST_CLEAN" if confirmed else "BUILDING"
    else:
        n = recent_activation_count(ep, stamp, int(policy.get("window_minutes", 10)))
        confirmed = n >= int(policy.get("min_observations", 2)) and ep.get("flip_count_30m", 0) <= int(policy.get("max_flips", 0))
        ep["ttt_state"] = "CONFIRMED_PERSISTENCE" if confirmed else "BUILDING"

    if not confirmed:
        ep["shadow_decision"] = "WAIT"
        ep["hysteresis_state"] = "NEUTRAL"
        return ep["shadow_decision"], False

    if not ep.get("confirmed_at"):
        ep["confirmed_at"] = stamp
        minutes = int((cfg.get("hysteresis") or {}).get("confirmation_memory_minutes", 15))
        ep["confirmation_memory_until"] = (parse_dt(stamp) + timedelta(minutes=minutes)).isoformat()
        ep["hysteresis_state"] = "CONFIRMED"
    else:
        ep["hysteresis_state"] = "CONFIRMED_HOLD"
    ep["shadow_decision"] = "ACCEPT"
    if not ep.get("authorization_emitted"):
        authorize = True
        ep["authorization_emitted"] = True
    ep["would_authorize_new_trade"] = authorize
    return ep["shadow_decision"], authorize


def ensure_episode(state: dict[str, Any], source: str, symbol: str, side: str, stamp: str, cfg: dict[str, Any]) -> dict[str, Any]:
    slot = episode_slot(source, symbol, side)
    active = state.setdefault("active_episodes", {})
    ep = active.get(slot)
    if should_start_new(ep, stamp, side, int(cfg.get("episode_gap_minutes", 15))):
        if ep:
            archived = dict(ep)
            archived["closed_at"] = ep.get("last_observation_at")
            state.setdefault("recent_episodes", []).append(archived)
            state["recent_episodes"] = state["recent_episodes"][-250:]
        seqs = state.setdefault("episode_sequences", {})
        seqs[source_key(source, symbol)] = int(seqs.get(source_key(source, symbol), 0)) + 1
        ep = new_episode(source, symbol, side, stamp, seqs[source_key(source, symbol)])
        active[slot] = ep
    ep["last_observation_at"] = stamp
    ep["updated_at"] = stamp
    ep["flip_count_30m"] = update_flip_memory(state, source, symbol, side, stamp, int(cfg.get("flicker_window_minutes", 30)))
    return ep


def apply_activation(state: dict[str, Any], obs: dict[str, Any], cfg: dict[str, Any]) -> dict[str, Any]:
    source, symbol, side = obs["source"], obs["symbol"], obs["side"]
    stamp = observation_time(obs)
    ep = ensure_episode(state, source, symbol, side, stamp, cfg)
    if stamp not in ep["activation_times"]:
        ep["activation_times"].append(stamp)
        ep["activation_times"] = ep["activation_times"][-20:]
    cid = obs.get("candidate_id")
    if cid and cid not in ep["candidate_ids"]:
        ep["candidate_ids"].append(cid)
    ep["would_authorize_new_trade"] = False
    recompute_episode(ep, cfg, stamp)
    return ep


def apply_meta_decision(state: dict[str, Any], row: dict[str, Any], cfg: dict[str, Any]) -> dict[str, Any]:
    source, symbol, side = str(row.get("source")), str(row.get("symbol")), str(row.get("side"))
    stamp = observation_time(row)
    ep = ensure_episode(state, source, symbol, side, stamp, cfg)
    ep["meta_decision_count"] = int(ep.get("meta_decision_count") or 0) + 1
    ep["latest_meta_decision"] = row.get("decision")
    ep["latest_meta_id"] = row.get("meta_decision_id")
    ep["latest_block_reasons"] = list(row.get("block_reasons") or [])
    ep["latest_wait_reasons"] = list(row.get("wait_reasons") or [])
    ep["strategy"] = row.get("strategy")
    ep["contract"] = row.get("contract")
    ep["market_regime"] = row.get("market_regime")
    for cid in row.get("candidate_ids") or []:
        if cid not in ep["candidate_ids"]:
            ep["candidate_ids"].append(cid)
    ep["would_authorize_new_trade"] = False
    recompute_episode(ep, cfg, stamp)
    return ep
