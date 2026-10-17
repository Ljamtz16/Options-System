from __future__ import annotations

from datetime import datetime
from statistics import median
from typing import Any


def num(value, default=None):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def stamp(value: str) -> datetime:
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def minutes(a: datetime, b: datetime) -> float:
    return (b - a).total_seconds() / 60.0


def max_drawdown(pnls: list[float]) -> float | None:
    if not pnls:
        return None
    equity = peak = worst = 0.0
    for pnl in pnls:
        equity += pnl
        peak = max(peak, equity)
        worst = min(worst, equity - peak)
    return worst


def _entry_replay(points: list[dict[str, Any]], idx: int, end_idx: int) -> dict[str, Any] | None:
    if idx < 0 or idx > end_idx:
        return None
    ask = num(points[idx].get("ask"))
    if ask is None or ask <= 0:
        return None
    marks = []
    for p in points[idx : end_idx + 1]:
        bid = num(p.get("bid"))
        if bid is not None and bid > 0:
            marks.append((bid / ask - 1.0, bid, p["time"]))
    if not marks:
        return None
    terminal, exit_bid, exit_time = marks[-1]
    return {
        "entry_time": points[idx]["time"].isoformat(),
        "entry_ask": ask,
        "exit_time": exit_time.isoformat(),
        "exit_bid": exit_bid,
        "terminal_return": terminal,
        "pnl_1_contract": (exit_bid - ask) * 100.0,
        "mfe": max(x[0] for x in marks),
        "mae": min(x[0] for x in marks),
        "marks": len(marks),
    }


def analyze_episode(
    *,
    strategy: str,
    source: str,
    evidence: str,
    symbol: str,
    side: str,
    signal_time: datetime,
    contract: str,
    initial_ask: float,
    horizon_minutes: int,
    points: list[dict[str, Any]],
    config: dict[str, Any],
) -> dict[str, Any]:
    end_time = signal_time.timestamp() + horizon_minutes * 60
    path = [p for p in sorted(points, key=lambda x: x["time"]) if signal_time <= p["time"] and p["time"].timestamp() <= end_time]
    path = [p for p in path if num(p.get("bid")) is not None and num(p.get("bid")) > 0]
    out = {
        "strategy": strategy,
        "source": source,
        "evidence": evidence,
        "symbol": symbol,
        "side": side,
        "signal_time": signal_time.isoformat(),
        "contract": contract,
        "initial_ask": initial_ask,
        "horizon_minutes": horizon_minutes,
        "path_points": len(path),
        "evaluable": False,
        "variants": {},
    }
    if initial_ask <= 0 or not path:
        return out
    refs = [num(p["bid"]) / initial_ask - 1.0 for p in path]
    out["evaluable"] = True
    out["mfe"] = max(refs)
    out["mae"] = min(refs)
    sl = float(config["sl_touch_return"])
    eps = 1e-12
    sl_idx = next((i for i, r in enumerate(refs) if r <= sl + eps), None)
    out["touched_sl10"] = sl_idx is not None
    out["sl_time"] = path[sl_idx]["time"].isoformat() if sl_idx is not None else None
    out["signal_to_sl_minutes"] = minutes(signal_time, path[sl_idx]["time"]) if sl_idx is not None else None
    if sl_idx is not None:
        post = refs[sl_idx:]
        min_rel = min(range(len(post)), key=lambda j: post[j])
        min_idx = sl_idx + min_rel
        out["post_sl_min_return"] = refs[min_idx]
        out["sl_to_min_minutes"] = minutes(path[sl_idx]["time"], path[min_idx]["time"])
        for target in config["post_sl_targets"]:
            key = f"post_sl_hit_{int(round(float(target)*100))}"
            idx = next((i for i in range(sl_idx + 1, len(path)) if refs[i] + eps >= float(target)), None)
            out[key] = idx is not None
            out[f"{key}_minutes"] = minutes(path[sl_idx]["time"], path[idx]["time"]) if idx is not None else None
    else:
        out["post_sl_min_return"] = None
        out["sl_to_min_minutes"] = None
        for target in config["post_sl_targets"]:
            key = f"post_sl_hit_{int(round(float(target)*100))}"
            out[key] = False
            out[f"{key}_minutes"] = None

    end_idx = len(path) - 1
    out["variants"]["ORIGINAL"] = _entry_replay(
        [{**p, "ask": initial_ask if i == 0 else p.get("ask")} for i, p in enumerate(path)], 0, end_idx
    )
    if sl_idx is None:
        for name in ("TOUCH10", "RECLAIM8", "REBOUND5"):
            out["variants"][name] = None
        return out

    out["variants"]["TOUCH10"] = _entry_replay(path, sl_idx, end_idx)
    reclaim = float(config["variants"]["RECLAIM8"]["reclaim_return"])
    reclaim_idx = next((i for i in range(sl_idx + 1, len(path)) if refs[i] + eps >= reclaim), None)
    out["variants"]["RECLAIM8"] = _entry_replay(path, reclaim_idx, end_idx) if reclaim_idx is not None else None
    out["reclaim8_minutes"] = minutes(path[sl_idx]["time"], path[reclaim_idx]["time"]) if reclaim_idx is not None else None

    rebound = float(config["variants"]["REBOUND5"]["rebound_points"])
    running_min = refs[sl_idx]
    rebound_idx = None
    for i in range(sl_idx + 1, len(path)):
        running_min = min(running_min, refs[i])
        if refs[i] + eps >= running_min + rebound:
            rebound_idx = i
            break
    out["variants"]["REBOUND5"] = _entry_replay(path, rebound_idx, end_idx) if rebound_idx is not None else None
    out["rebound5_minutes"] = minutes(path[sl_idx]["time"], path[rebound_idx]["time"]) if rebound_idx is not None else None
    return out


def summarize(episodes: list[dict[str, Any]]) -> dict[str, Any]:
    evaluable = [e for e in episodes if e.get("evaluable")]
    touched = [e for e in evaluable if e.get("touched_sl10")]
    out: dict[str, Any] = {
        "episodes": len(episodes),
        "evaluable": len(evaluable),
        "touched_sl10": len(touched),
        "touched_sl10_rate": len(touched) / len(evaluable) if evaluable else None,
        "mean_mae": sum(e["mae"] for e in evaluable) / len(evaluable) if evaluable else None,
        "mean_mfe": sum(e["mfe"] for e in evaluable) / len(evaluable) if evaluable else None,
    }
    for target in (10, 20, 30):
        key = f"post_sl_hit_{target}"
        hits = [e for e in touched if e.get(key)]
        out[f"sl10_then_{target}"] = len(hits)
        out[f"sl10_then_{target}_rate"] = len(hits) / len(touched) if touched else None
        times = [e.get(f"{key}_minutes") for e in hits if e.get(f"{key}_minutes") is not None]
        out[f"median_sl_to_{target}_minutes"] = median(times) if times else None
    mins = [e.get("post_sl_min_return") for e in touched if e.get("post_sl_min_return") is not None]
    out["median_post_sl_min_return"] = median(mins) if mins else None
    for timing in ("signal_to_sl_minutes", "sl_to_min_minutes", "reclaim8_minutes", "rebound5_minutes"):
        vals = [e.get(timing) for e in touched if e.get(timing) is not None]
        out[f"median_{timing}"] = median(vals) if vals else None

    original = [e.get("variants", {}).get("ORIGINAL") for e in evaluable]
    original = [x for x in original if x]
    for name in ("ORIGINAL", "TOUCH10", "RECLAIM8", "REBOUND5"):
        vals = [e.get("variants", {}).get(name) for e in evaluable]
        entered = [x for x in vals if x]
        pnls = [x["pnl_1_contract"] for x in entered]
        mfe = [x["mfe"] for x in entered]
        mae = [x["mae"] for x in entered]
        missed = avoided = 0
        if name != "ORIGINAL":
            for e in evaluable:
                if e.get("variants", {}).get(name) is not None:
                    continue
                base = e.get("variants", {}).get("ORIGINAL")
                if not base:
                    continue
                if base["pnl_1_contract"] > 0:
                    missed += 1
                else:
                    avoided += 1
        out.setdefault("variants", {})[name] = {
            "entries": len(entered),
            "entry_rate": len(entered) / len(evaluable) if evaluable else None,
            "wins": sum(p > 0 for p in pnls),
            "win_rate": sum(p > 0 for p in pnls) / len(pnls) if pnls else None,
            "total_pnl_1_contract": sum(pnls) if pnls else None,
            "mean_pnl_1_contract": sum(pnls) / len(pnls) if pnls else None,
            "mean_mfe": sum(mfe) / len(mfe) if mfe else None,
            "mean_mae": sum(mae) / len(mae) if mae else None,
            "max_drawdown_pnl": max_drawdown(pnls),
            "winners_missed": missed,
            "losers_avoided": avoided,
        }
    return out
