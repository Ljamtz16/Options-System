from datetime import datetime
from options_system.option_costs import one_contract_trade, daily_regulatory_fees

def _active(row,hypothesis_id):
    return hypothesis_id in [x for x in (row.get("active_hypotheses") or "").split(";") if x]

def build_episodes(rows,hypothesis):
    policy=hypothesis.get("episode_policy")
    if not policy:return []
    hid=hypothesis["id"];gap=float(policy.get("gap_minutes",0));start_after=hypothesis.get("prospective_start_after")
    active=[r for r in rows if _active(r,hid) and (not start_after or r.get("decision_date","")>start_after)]
    active.sort(key=lambda r:r.get("captured_at_utc",""))
    grouped=[];current=None;previous=None
    for row in active:
        ts=datetime.fromisoformat(row["captured_at_utc"])
        new_day=current is not None and row.get("decision_date")!=current["decision_date"]
        if current is None or previous is None or new_day or (ts-previous).total_seconds()>gap*60:
            current={"decision_date":row.get("decision_date"),"rows":[row]};grouped.append(current)
        else:current["rows"].append(row)
        previous=ts
    side=hypothesis["side"];hz=int(hypothesis["horizon_min"]);episodes=[]
    for i,g in enumerate(grouped,1):
        entry=g["rows"][0];touch=entry.get(f"{side}_{hz}m_tp10_sl10");exit_return=entry.get(f"{side}_{hz}m_tp10_sl10_exit_return")
        trade=one_contract_trade(entry.get(f"{side}_entry_ask"),exit_return)
        episodes.append({"hypothesis":hid,"episode_id":f"{hid}:{g['decision_date']}:E{i}",
          "decision_date":g["decision_date"],"start":entry.get("captured_at_utc"),"end":g["rows"][-1].get("captured_at_utc"),
          "activation_count":len(g["rows"]),"side":side,"horizon_min":hz,"contract":entry.get(f"{side}_contract"),
          "entry_bid":entry.get(f"{side}_entry_bid"),"entry_ask":entry.get(f"{side}_entry_ask"),
          "entry_bid_size":entry.get(f"{side}_entry_bid_size"),"entry_ask_size":entry.get(f"{side}_entry_ask_size"),
          "return":entry.get(f"{side}_ret_{hz}m"),
          "mfe":entry.get(f"{side}_mfe_{hz}m"),"mae":entry.get(f"{side}_mae_{hz}m"),"tp_sl":touch,
          "exit_return":exit_return,"trade_1_contract":trade})
    return episodes

def build_virtual_account(episodes,initial_cash=1000.0):
    cash=float(initial_cash);ledger=[]
    ordered=sorted(episodes,key=lambda e:(e.get("decision_date",""),e.get("start","")))
    for e in ordered:
        t=e.get("trade_1_contract");before=cash
        if not t:
            status="PENDING_OUTCOME";fee=0.0;gross=0.0;net=0.0
        elif t["capital_required"]>cash:
            status="SKIP_INSUFFICIENT_CASH";fee=0.0;gross=0.0;net=0.0
        else:
            status="EXECUTED";gross=float(t["gross_pnl"])
            fee=float(daily_regulatory_fees([t])["total"])
            net=gross-fee;cash+=net
        ledger.append({**e,"account_status":status,
          "cash_before_trade":before,"trade_gross_pnl":gross,"trade_fees":fee,
          "trade_net_pnl":net,"cash_after_trade":cash})
    for day in sorted({x["decision_date"] for x in ledger}):
        items=[x for x in ledger if x["decision_date"]==day]
        day_gross=sum(x["trade_gross_pnl"] for x in items)
        day_fees=sum(x["trade_fees"] for x in items)
        day_net=sum(x["trade_net_pnl"] for x in items)
        day_open=items[0]["cash_before_trade"];day_close=items[-1]["cash_after_trade"]
        for x in items:
            x["cash_before"]=day_open;x["day_gross_pnl"]=day_gross;x["day_fees"]=day_fees
            x["day_net_pnl"]=day_net;x["cash_after_day"]=day_close
    return {"initial_cash":float(initial_cash),"final_cash":cash,
      "net_pnl":cash-float(initial_cash),"ledger":ledger}
