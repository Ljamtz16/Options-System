from __future__ import annotations

from datetime import datetime
from typing import Any

from options_system.meta_decision_layer import decision_from_reasons, market_regime, num


def health_flags_from_closed(closed: list[dict[str, Any]], vix_change_pct: Any) -> list[str]:
    ordered = sorted(closed, key=lambda r: str(r.get("exit_time") or r.get("signal_time") or ""))
    flags: list[str] = []
    streak = 0
    for row in reversed(ordered):
        pnl = num(row.get("net_pnl"))
        if pnl is not None and pnl <= 0:
            streak += 1
        else:
            break
    if streak >= 4:
        flags.append("loss_streak_4")
    last5 = ordered[-5:]
    if len(last5) == 5:
        vals = [num(r.get("net_pnl")) for r in last5]
        if all(v is not None for v in vals) and sum(v > 0 for v in vals) / 5 <= 0.20:
            flags.append("rolling5_winrate_below_20pct")
    vix = num(vix_change_pct)
    if vix is not None and vix >= 0.05:
        flags.append("vix_up_5pct")
    return flags


def episode_metrics(history: list[dict[str, Any]], source: str, symbol: str, side: str, stamp: str,
                    gap_minutes: int = 15, flicker_minutes: int = 30) -> dict[str, Any]:
    now = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    relevant = [r for r in history if r.get("source") == source and r.get("symbol") == symbol]
    relevant.sort(key=lambda r: str(r.get("time")))
    last = relevant[-1] if relevant else None
    new_episode = True
    if last:
        prev = datetime.fromisoformat(str(last["time"]).replace("Z", "+00:00"))
        new_episode = (now - prev).total_seconds() > gap_minutes * 60 or str(last.get("side")) != side
    if new_episode:
        episode_no = 1 + max([int(r.get("episode_no") or 0) for r in relevant] or [0])
        episode_start = now
        observations = 1
    else:
        episode_no = int(last.get("episode_no") or 1)
        episode_start = datetime.fromisoformat(str(last.get("episode_start") or last["time"]).replace("Z", "+00:00"))
        observations = int(last.get("persistence_observations") or 1) + 1
    recent = []
    for row in relevant:
        t = datetime.fromisoformat(str(row["time"]).replace("Z", "+00:00"))
        if (now - t).total_seconds() <= flicker_minutes * 60:
            recent.append(row)
    sides = [str(r.get("side") or "NONE") for r in recent] + [side]
    flips = sum(a != b for a, b in zip(sides, sides[1:]))
    return {
        "episode_no": episode_no,
        "episode_id": f"{source}:{symbol}:{now.date().isoformat()}:E{episode_no}",
        "episode_start": episode_start.isoformat(),
        "persistence_observations": observations,
        "persistence_minutes": round((now - episode_start).total_seconds() / 60.0, 3),
        "is_episode_repeat": not new_episode,
        "signal_flip_count_30m": flips,
    }


def h01_decision(executable: bool, flags: list[str], regime: str, repeated: bool,
                 context_ready: bool = True) -> tuple[str, list[str], list[str]]:
    block: list[str] = []
    wait: list[str] = []
    if not executable:
        block.append("EXECUTION_CONTRACT_FAIL")
    for flag in ("loss_streak_4", "rolling5_winrate_below_20pct", "vix_up_5pct"):
        if flag in flags:
            block.append(f"HEALTH:{flag}")
    if not context_ready:
        wait.append("CONTEXT_NOT_READY")
    elif regime == "RISK_OFF":
        block.append("REGIME:risk_off_regime")
    if repeated:
        wait.append("CORRELATED_REPEAT_WITHIN_15M")
    return decision_from_reasons(block, wait), block, wait


def h09_decision(is_h09b: bool, contract: Any, ask: Any, bid: Any, regime: str,
                 max_price: float, max_spread: float) -> tuple[str, list[str], list[str], float | None]:
    block: list[str] = []
    wait: list[str] = []
    a, b = num(ask), num(bid)
    spread = (a - b) / a if a and b is not None and a > 0 else None
    if not contract or a is None or a <= 0 or a > max_price:
        block.append("EXECUTION:CONTRACT_OR_PRICE")
    if spread is not None and spread > max_spread:
        block.append("EXECUTION:SPREAD")
    if is_h09b and regime != "RISK_OFF":
        block.append("REGIME:H09B_NOT_RISK_OFF")
    if not is_h09b:
        wait.append("REGIME:WAIT_FOR_RISK_OFF_CONFIRMATION")
    return decision_from_reasons(block, wait), block, wait, spread


def multi_decision(side: str, contract: Any, ask: Any, bid: Any, regime: str, support_count: int,
                   max_price: float, max_spread: float, redundant_ge: int = 2) -> tuple[str, list[str], list[str], float | None]:
    block: list[str] = []
    wait: list[str] = []
    a, b = num(ask), num(bid)
    spread = (a - b) / a if a and b is not None and a > 0 else None
    if not contract or a is None or a <= 0 or a > max_price:
        block.append("EXECUTION:CONTRACT_OR_PRICE")
    if spread is not None and spread > max_spread:
        block.append("EXECUTION:SPREAD")
    desired = "RISK_ON" if side.upper() == "CALL" else "RISK_OFF"
    if regime != desired:
        block.append(f"REGIME:REQUIRE_{desired}")
    if support_count >= redundant_ge:
        wait.append("REDUNDANT_SUPPORT_NOT_CONFIRMATION")
    return decision_from_reasons(block, wait), block, wait, spread




def context_ready_for_day(context: dict[str, Any], day: str) -> bool:
    stamp = str(context.get("captured_at_utc") or "")
    return bool(stamp and day and stamp[:10] == str(day))

def context_from_envelope(envelope: dict[str, Any]) -> dict[str, Any]:
    payload = envelope.get("payload") or {}
    research = (payload.get("research_state") or {}).get("features") or {}
    cross = (payload.get("cross_market") or {}).get("features") or {}
    global_ctx = payload.get("global_context") or {}
    global_cross = global_ctx.get("cross_market") or {}
    vix = global_ctx.get("vix") or payload.get("vix") or {}
    def first(*vals):
        for value in vals:
            if value not in (None, ""):
                return value
        return None
    spy = first(research.get("spy_from_open"), cross.get("spy_from_open"), global_cross.get("spy_from_open"))
    qqq = first(research.get("qqq_from_open"), cross.get("qqq_from_open"), global_cross.get("qqq_from_open"))
    iwm = first(research.get("iwm_from_open"), cross.get("iwm_from_open"), global_cross.get("iwm_from_open"))
    vix_pct = first(research.get("vix_change_pct"), vix.get("change_pct"), vix.get("vix_change_pct"))
    return {
        "captured_at_utc": envelope.get("captured_at_utc"),
        "spy_from_open": num(spy), "qqq_from_open": num(qqq), "iwm_from_open": num(iwm),
        "vix_change_pct": num(vix_pct),
        "market_regime": market_regime(spy, qqq, iwm),
    }
