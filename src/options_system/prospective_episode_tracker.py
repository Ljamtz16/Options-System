from datetime import datetime
from options_system.option_costs import one_contract_trade, daily_regulatory_fees

def _active(row, hypothesis_id):
    return hypothesis_id in [x for x in (row.get("active_hypotheses") or "").split(";") if x]

def build_episodes(rows, hypothesis):
    policy=hypothesis.get("episode_policy")
    if not policy:
        return []
    hid=hypothesis["id"]
    gap=float(policy.get("gap_minutes", 0))
    start_after=hypothesis.get("prospective_start_after")
    active=[r for r in rows if _active(r,hid) and (not start_after or r.get("decision_date","")>start_after)]
    active.sort(key=lambda r:r.get("captured_at_utc",""))
    grouped=[]; current=None; previous=None
    for row in active:
        ts=datetime.fromisoformat(row["captured_at_utc"])
        new_day=current is not None and row.get("decision_date") != current["decision_date"]
        if current is None or previous is None or new_day or (ts-previous).total_seconds()>gap*60:
            current={"decision_date":row.get("decision_date"),"rows":[row]}
            grouped.append(current)
        else:
            current["rows"].append(row)
        previous=ts
    side=hypothesis["side"]; hz=int(hypothesis["horizon_min"])
    episodes=[]
    for i,g in enumerate(grouped,1):
        entry=g["rows"][0]
        touch=entry.get(f"{side}_{hz}m_tp10_sl10")
        exit_return=entry.get(f"{side}_{hz}m_tp10_sl10_exit_return")
        trade=one_contract_trade(entry.get(f"{side}_entry_ask"),exit_return)
        episodes.append({
            "hypothesis":hid,
            "episode_id":f"{hid}:{g['decision_date']}:E{i}",
            "decision_date":g["decision_date"],
            "start":entry.get("captured_at_utc"),
            "end":g["rows"][-1].get("captured_at_utc"),
            "activation_count":len(g["rows"]),
            "side":side,
            "horizon_min":hz,
            "contract":entry.get(f"{side}_contract"),
            "entry_ask":entry.get(f"{side}_entry_ask"),
            "return":entry.get(f"{side}_ret_{hz}m"),
            "mfe":entry.get(f"{side}_mfe_{hz}m"),
            "mae":entry.get(f"{side}_mae_{hz}m"),
            "tp_sl":touch,
            "exit_return":exit_return,
            "trade_1_contract":trade,
        })
    return episodes

def build_virtual_account(episodes, initial_cash=1000.0):
    cash=float(initial_cash); ledger=[]
    days=sorted({e["decision_date"] for e in episodes})
    for day in days:
        day_eps=[e for e in episodes if e["decision_date"]==day]
        executed=[]
        for e in day_eps:
            t=e.get("trade_1_contract")
            if not t:
                status="PENDING_OUTCOME"
            elif t["capital_required"]>cash:
                status="SKIP_INSUFFICIENT_CASH"
            else:
                status="EXECUTED"; executed.append((e,t))
            ledger.append({**e,"account_status":status,"cash_before":cash})
        fees=daily_regulatory_fees([t for _,t in executed]) if executed else {"components":{},"total":0.0}
        gross=sum(t["gross_pnl"] for _,t in executed)
        cash+=gross-fees["total"]
        for item in ledger:
            if item["decision_date"]==day:
                item["day_gross_pnl"]=gross
                item["day_fees"]=fees["total"]
                item["day_net_pnl"]=gross-fees["total"]
                item["cash_after_day"]=cash
    return {"initial_cash":float(initial_cash),"final_cash":cash,"net_pnl":cash-float(initial_cash),"ledger":ledger}
