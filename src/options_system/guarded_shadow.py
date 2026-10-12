"""Shadow-only guardrail replay for frozen Local Paper trades."""
from __future__ import annotations
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Any

NY = ZoneInfo("America/New_York")
DEFAULT_CONFIG = {
    "target_hypotheses": ["CALL_FLOW_REVERSAL_V01"],
    "halt_after_consecutive_losses": 4,
    "minimum_halt_minutes": 30,
    "spy_momentum_minutes": 10,
    "spy_momentum_gt": 0.0,
    "no_new_low_lookback_minutes": 15,
}

def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))

def _day(value: datetime) -> str:
    return value.astimezone(NY).date().isoformat()

def _tracker_index(rows: list[dict[str, Any]]):
    out = {}
    for row in rows:
        ts_s = row.get("captured_at_utc")
        price = row.get("spy_price") or row.get("spot")
        if not ts_s or price in (None, ""):
            continue
        try:
            ts, px = _dt(str(ts_s)), float(price)
        except (TypeError, ValueError):
            continue
        out.setdefault(_day(ts), []).append((ts, px))
    for day in out:
        out[day].sort(key=lambda x: x[0])
    return out

def _market_context(index, now, cfg):
    rows = [(ts, px) for ts, px in index.get(_day(now), []) if ts <= now]
    if not rows:
        return {"spy_price": None, "spy_momentum": None, "no_new_low": False, "market_context_ready": False}
    current_ts, current_px = rows[-1]
    mcut = now - timedelta(minutes=int(cfg["spy_momentum_minutes"]))
    prior = [(ts, px) for ts, px in rows if ts <= mcut]
    momentum = current_px / prior[-1][1] - 1.0 if prior and prior[-1][1] else None
    lcut = now - timedelta(minutes=int(cfg["no_new_low_lookback_minutes"]))
    before = [px for ts, px in rows if ts <= lcut]
    recent = [px for ts, px in rows if ts > lcut]
    no_new_low = bool(before and recent and min(recent) > min(before))
    return {
        "spy_price": current_px, "spy_price_time": current_ts.isoformat(),
        "spy_momentum": momentum, "spy_momentum_minutes": int(cfg["spy_momentum_minutes"]),
        "prior_session_low": min(before) if before else None,
        "recent_low": min(recent) if recent else None,
        "no_new_low": no_new_low,
        "no_new_low_lookback_minutes": int(cfg["no_new_low_lookback_minutes"]),
        "market_context_ready": momentum is not None and bool(before and recent),
    }

def build_guarded_shadow(live_state, tracker_rows, config=None, generated_at=None):
    cfg = {**DEFAULT_CONFIG, **(config or {})}
    targets = set(cfg["target_hypotheses"])
    halt_n = int(cfg["halt_after_consecutive_losses"])
    min_halt = int(cfg["minimum_halt_minutes"])
    market = _tracker_index(tracker_rows)
    trades = []
    source = list(live_state.get("live_ledger") or []) + list(live_state.get("open_positions") or [])
    for row in source:
        if row.get("hypothesis") not in targets or row.get("status") not in {"CLOSED", "OPEN"}:
            continue
        entry_s = row.get("entry_time") or row.get("signal_time")
        if not entry_s:
            continue
        item = dict(row)
        item["_entry_dt"] = _dt(entry_s)
        item["_exit_dt"] = _dt(row["exit_time"]) if row.get("status") == "CLOSED" and row.get("exit_time") else None
        trades.append(item)
    events = []
    for trade in trades:
        events.append((trade["_entry_dt"], 1, "ENTRY", trade))
        if trade["_exit_dt"] is not None:
            events.append((trade["_exit_dt"], 0, "EXIT", trade))
    events.sort(key=lambda x: (x[0], x[1], x[3].get("signal_id", "")))
    day_state, entered, decisions, decision_by_id, transitions = {}, {}, [], {}, []
    for ts, _order, kind, trade in events:
        day = _day(ts)
        st = day_state.setdefault(day, {"state":"ACTIVE","consecutive_losses":0,"halted_at":None,"halts":0,"rearms":0})
        sid = str(trade.get("signal_id"))
        if kind == "ENTRY":
            ctx = _market_context(market, ts, cfg)
            action, reason, rearmed = "WOULD_ENTER", "ACTIVE", False
            if st["state"] == "HALTED":
                halted_at = st.get("halted_at")
                elapsed = (ts - halted_at).total_seconds()/60.0 if halted_at else 0.0
                momentum_ok = ctx.get("spy_momentum") is not None and float(ctx["spy_momentum"]) > float(cfg["spy_momentum_gt"])
                low_ok = bool(ctx.get("no_new_low")); time_ok = elapsed >= min_halt
                ready = bool(ctx.get("market_context_ready"))
                if time_ok and momentum_ok and low_ok and ready:
                    st.update(state="ACTIVE", consecutive_losses=0, halted_at=None)
                    st["rearms"] += 1; rearmed = True; reason = "REARMED_REGIME"
                    transitions.append({"timestamp":ts.isoformat(),"decision_date":day,"type":"REARM","signal_id":sid,"elapsed_halt_minutes":elapsed,"market_context":ctx})
                else:
                    action = "WOULD_SKIP"; failed = []
                    if not time_ok: failed.append("MIN_HALT_TIME")
                    if not momentum_ok: failed.append("SPY_MOMENTUM_10M")
                    if not low_ok: failed.append("NO_NEW_LOW_15M")
                    if not ready: failed.append("MARKET_CONTEXT_READY")
                    reason = "HALTED:" + ",".join(failed)
            entered[sid] = action == "WOULD_ENTER"
            decision = {"signal_id":sid,"hypothesis":trade.get("hypothesis"),"decision_date":day,
                        "entry_time":trade.get("entry_time") or trade.get("signal_time"),"frozen_status":trade.get("status"),
                        "shadow_action":action,"shadow_reason":reason,"state_at_decision":"REARMED" if rearmed else st["state"],
                        "consecutive_losses_before_entry":st["consecutive_losses"],"market_context":ctx,
                        "frozen_exit_reason":trade.get("exit_reason"),"frozen_net_pnl":trade.get("net_pnl")}
            decisions.append(decision); decision_by_id[sid] = decision
            continue
        if not entered.get(sid):
            continue
        pnl = trade.get("net_pnl")
        if pnl is None:
            continue
        pnl = float(pnl)
        st["consecutive_losses"] = st["consecutive_losses"] + 1 if pnl < 0 else 0
        if sid in decision_by_id:
            decision_by_id[sid]["shadow_realized_net_pnl"] = pnl
        if halt_n > 0 and st["state"] == "ACTIVE" and st["consecutive_losses"] >= halt_n:
            st["state"] = "HALTED"; st["halted_at"] = ts; st["halts"] += 1
            transitions.append({"timestamp":ts.isoformat(),"decision_date":day,"type":"HALT","signal_id":sid,
                                "consecutive_losses":st["consecutive_losses"],"trigger":f"{halt_n}_CONSECUTIVE_LOSSES"})

    frozen_closed = [d for d in decisions if d.get("frozen_net_pnl") is not None]
    entered_closed = [d for d in frozen_closed if d["shadow_action"] == "WOULD_ENTER"]
    skipped_closed = [d for d in frozen_closed if d["shadow_action"] == "WOULD_SKIP"]
    by_day = {}
    for day in sorted({d["decision_date"] for d in decisions}):
        ds = [d for d in decisions if d["decision_date"] == day]
        closed = [d for d in ds if d.get("frozen_net_pnl") is not None]
        kept = [d for d in closed if d["shadow_action"] == "WOULD_ENTER"]
        skipped = [d for d in closed if d["shadow_action"] == "WOULD_SKIP"]
        frozen_pnl = sum(float(d["frozen_net_pnl"]) for d in closed)
        guarded_pnl = sum(float(d["frozen_net_pnl"]) for d in kept)
        by_day[day] = {
            "frozen_trades":len(closed),"guarded_trades":len(kept),"skipped_trades":len(skipped),
            "frozen_net_pnl":frozen_pnl,"guarded_net_pnl":guarded_pnl,"pnl_difference":guarded_pnl-frozen_pnl,
            "sl_avoided":sum(d.get("frozen_exit_reason")=="SL10" for d in skipped),
            "tp_sacrificed":sum(d.get("frozen_exit_reason")=="TP10" for d in skipped),
            "halts":day_state.get(day,{}).get("halts",0),"rearms":day_state.get(day,{}).get("rearms",0),
            "ending_shadow_state":day_state.get(day,{}).get("state","ACTIVE")}
    frozen_pnl = sum(float(d["frozen_net_pnl"]) for d in frozen_closed)
    guarded_pnl = sum(float(d["frozen_net_pnl"]) for d in entered_closed)
    return {
        "version":"guarded_shadow_v01","mode":"COUNTERFACTUAL_SHADOW_ONLY","account_kind":"LOCAL_SIMULATION_SHADOW",
        "scientific_frozen_unchanged":True,"generated_at":(generated_at or datetime.now().astimezone()).isoformat(),
        "configuration":cfg,
        "summary":{"frozen_closed_trades":len(frozen_closed),"guarded_closed_trades":len(entered_closed),
                   "skipped_closed_trades":len(skipped_closed),"frozen_net_pnl":frozen_pnl,"guarded_net_pnl":guarded_pnl,
                   "pnl_difference":guarded_pnl-frozen_pnl,
                   "sl_avoided":sum(d.get("frozen_exit_reason")=="SL10" for d in skipped_closed),
                   "tp_sacrificed":sum(d.get("frozen_exit_reason")=="TP10" for d in skipped_closed),
                   "halts":sum(s.get("halts",0) for s in day_state.values()),"rearms":sum(s.get("rearms",0) for s in day_state.values())},
        "by_day":by_day,"transitions":transitions,"decisions":decisions}
