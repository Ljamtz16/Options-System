#!/usr/bin/env python3
from __future__ import annotations

import bisect
import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, median
from urllib.request import urlopen
from zoneinfo import ZoneInfo

from options_system.multisymbol_shadow import derive_row, active_candidates, is_new_episode, signal_key

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts/intraday"
TRACKER = ROOT / "data/processed/intraday/prospective_hypothesis_tracker_v02.csv"
MULTI_DATA = ROOT / "data/processed/intraday/intraday_options_v2.csv"
MULTI_CFG = ROOT / "config/multisymbol_shadow_v01.json"
OUT = ART / "SYSTEM_RESEARCH_DIAGNOSTICS_V01.json"
NY = ZoneInfo("America/New_York")


def num(v):
    try:
        x = float(v)
        return x if math.isfinite(x) else None
    except (TypeError, ValueError):
        return None


def dt(v):
    return datetime.fromisoformat(str(v).replace("Z", "+00:00"))


def avg(xs):
    vals = [x for x in xs if x is not None]
    return sum(vals) / len(vals) if vals else None


def med(xs):
    vals = sorted(x for x in xs if x is not None)
    return median(vals) if vals else None


def quantile(xs, p):
    vals = sorted(x for x in xs if x is not None)
    if not vals:
        return None
    if len(vals) == 1:
        return vals[0]
    k = (len(vals) - 1) * p
    lo, hi = int(math.floor(k)), int(math.ceil(k))
    if lo == hi:
        return vals[lo]
    return vals[lo] * (hi - k) + vals[hi] * (k - lo)


def stat(rows, ret_key="ret", pnl_key="pnl", mfe_key="mfe", mae_key="mae"):
    rets = [num(r.get(ret_key)) for r in rows]
    rets = [x for x in rets if x is not None]
    pnls = [num(r.get(pnl_key)) for r in rows]
    pnls = [x for x in pnls if x is not None]
    mfes = [num(r.get(mfe_key)) for r in rows]
    maes = [num(r.get(mae_key)) for r in rows]
    return {
        "n": len(rows),
        "return_n": len(rets),
        "mean_return": avg(rets),
        "median_return": med(rets),
        "win_rate": (sum(x > 0 for x in rets) / len(rets)) if rets else None,
        "net_pnl": sum(pnls) if pnls else None,
        "mean_pnl": avg(pnls),
        "mfe": {"mean": avg(mfes), "p25": quantile(mfes, .25), "p50": quantile(mfes, .5), "p75": quantile(mfes, .75)},
        "mae": {"mean": avg(maes), "p25": quantile(maes, .25), "p50": quantile(maes, .5), "p75": quantile(maes, .75)},
    }


def path_stat(rows, side, horizon=60, tp=10, sl=10):
    key = f"{side}_{horizon}m_tp{tp}_sl{sl}"
    term = f"{side}_terminal_return_{horizon}m"
    c = Counter(str(r.get(key) or "") for r in rows)
    policy = []
    for r in rows:
        p = str(r.get(key) or "")
        if p == "TP_FIRST": policy.append(tp / 100.0)
        elif p == "SL_FIRST": policy.append(-sl / 100.0)
        elif p == "NEITHER":
            x = num(r.get(term))
            if x is not None: policy.append(x)
    decided = c["TP_FIRST"] + c["SL_FIRST"]
    return {"n": len(rows), "tp_first": c["TP_FIRST"], "sl_first": c["SL_FIRST"], "neither": c["NEITHER"],
            "tp_first_rate_decided": c["TP_FIRST"] / decided if decided else None, "mean_policy_return": avg(policy)}


def load_tracker():
    rows = list(csv.DictReader(TRACKER.open(encoding="utf-8")))
    by_day = defaultdict(list)
    for r in rows:
        by_day[r.get("decision_date")].append(r)
    index = {}
    for day, items in by_day.items():
        items.sort(key=lambda r: r["captured_at_utc"])
        times = [dt(r["captured_at_utc"]).timestamp() for r in items]
        index[day] = (times, items)
    return rows, index


def nearest(index, day, when, max_seconds=95):
    if day not in index:
        return None
    times, rows = index[day]
    target = dt(when).timestamp()
    i = bisect.bisect_left(times, target)
    cand = []
    if i < len(times): cand.append((abs(times[i] - target), rows[i]))
    if i: cand.append((abs(times[i-1] - target), rows[i-1]))
    if not cand:
        return None
    gap, row = min(cand, key=lambda x: x[0])
    return row if gap <= max_seconds else None


def lookback(index, day, when, minutes=30):
    if day not in index:
        return None
    times, rows = index[day]
    target = dt(when).timestamp() - minutes * 60
    i = bisect.bisect_left(times, target)
    choices = []
    if i < len(times): choices.append((abs(times[i]-target), rows[i]))
    if i: choices.append((abs(times[i-1]-target), rows[i-1]))
    return min(choices, key=lambda x:x[0])[1] if choices else None


def regime_from_values(spy, qqq, iwm, vix=None, prior=None):
    vals = [num(spy), num(qqq), num(iwm)]
    if any(v is None for v in vals):
        return "UNKNOWN"
    cur = "ON" if all(v > 0 for v in vals) else "OFF" if all(v < 0 for v in vals) else "MIXED"
    if prior:
        pvals = [num(x) for x in prior]
        if all(v is not None for v in pvals):
            prev = "ON" if all(v > 0 for v in pvals) else "OFF" if all(v < 0 for v in pvals) else "MIXED"
            if prev == "OFF" and cur == "ON": return "REVERSAL_UP"
            if prev == "ON" and cur == "OFF": return "REVERSAL_DOWN"
    vx = num(vix)
    if cur == "ON": return "RISK_ON_CONFIRMED" if vx is not None and vx <= 0 else "RISK_ON"
    if cur == "OFF": return "RISK_OFF_CONFIRMED" if vx is not None and vx >= 0 else "RISK_OFF"
    return "CHOP_MIXED"


def h01_analysis(tracker_index):
    state = json.loads((ART / "PAPER_TRADING_LIVE_STATE_V01.json").read_text())
    trades = [dict(x) for x in state.get("live_ledger", []) if x.get("hypothesis") == "CALL_FLOW_REVERSAL_V01" and x.get("status") == "CLOSED"]
    trades.sort(key=lambda x: x.get("entry_time") or x.get("signal_time") or "")
    for t in trades:
        t["ret"] = (num(t.get("exit_bid")) / num(t.get("entry_ask")) - 1) if num(t.get("exit_bid")) and num(t.get("entry_ask")) else None
        t["pnl"] = num(t.get("net_pnl"))
        row = nearest(tracker_index, t.get("decision_date"), t.get("signal_time") or t.get("entry_time"))
        t["tracker"] = row
        prior = lookback(tracker_index, t.get("decision_date"), t.get("signal_time") or t.get("entry_time"), 30)
        pvals = [prior.get("spy_from_open"), prior.get("qqq_from_open"), prior.get("iwm_from_open")] if prior else None
        t["regime"] = regime_from_values(row.get("spy_from_open"), row.get("qqq_from_open"), row.get("iwm_from_open"), row.get("vix_change_pct"), pvals) if row else "UNKNOWN"
        t["vix_change_pct"] = num(row.get("vix_change_pct")) if row else None

    by_day = {}
    for day in sorted(set(t.get("decision_date") for t in trades)):
        xs = [t for t in trades if t.get("decision_date") == day]
        start = num(xs[0].get("cash_before")) if xs else None
        equity = start or 0.0; peak = equity; maxdd = 0.0; streak = maxstreak = 0
        for t in xs:
            equity += num(t.get("net_pnl")) or 0
            peak = max(peak, equity)
            if peak: maxdd = max(maxdd, (peak-equity)/peak)
            if (num(t.get("net_pnl")) or 0) < 0: streak += 1; maxstreak = max(maxstreak, streak)
            else: streak = 0
        s = stat(xs)
        s.update({"start_cash": start, "end_cash": equity, "max_drawdown_pct": maxdd, "max_loss_streak": maxstreak})
        by_day[day] = s

    by_regime = {r: stat([t for t in trades if t.get("regime") == r]) for r in sorted(set(t.get("regime") for t in trades))}

    # Correlation/overlap diagnostics.
    overlap_rows = []
    for t in trades:
        et = dt(t["entry_time"])
        active = [p for p in trades if p is not t and p.get("decision_date") == t.get("decision_date") and dt(p["entry_time"]) < et < dt(p["exit_time"])]
        row = dict(t); row["overlap_count"] = len(active); overlap_rows.append(row)
    overlap = {
        "standalone": stat([x for x in overlap_rows if x["overlap_count"] == 0]),
        "entered_while_h01_open": stat([x for x in overlap_rows if x["overlap_count"] >= 1]),
        "by_overlap_count": {str(k): stat([x for x in overlap_rows if x["overlap_count"] == k]) for k in sorted(set(x["overlap_count"] for x in overlap_rows))},
    }

    def selected_summary(selected): return stat(selected)
    def max_concurrent(k):
        out=[]
        for day in sorted(set(t["decision_date"] for t in trades)):
            chosen=[]
            for t in [x for x in trades if x["decision_date"]==day]:
                et=dt(t["entry_time"]); open_now=[x for x in chosen if dt(x["exit_time"])>et]
                if len(open_now)<k: chosen.append(t); out.append(t)
        return out
    def cooldown(minutes):
        out=[]
        for day in sorted(set(t["decision_date"] for t in trades)):
            last=None
            for t in [x for x in trades if x["decision_date"]==day]:
                et=dt(t["entry_time"])
                if last is None or (et-last).total_seconds() >= minutes*60:
                    out.append(t); last=et
        return out
    def halt_after_losses(n):
        out=[]
        for day in sorted(set(t["decision_date"] for t in trades)):
            streak=0; halted=False
            for t in [x for x in trades if x["decision_date"]==day]:
                if halted: continue
                out.append(t)
                if (num(t.get("net_pnl")) or 0)<0: streak+=1
                else: streak=0
                if streak>=n: halted=True
        return out
    def loss_limit(frac):
        out=[]
        for day in sorted(set(t["decision_date"] for t in trades)):
            xs=[x for x in trades if x["decision_date"]==day]
            if not xs: continue
            start=num(xs[0].get("cash_before")) or 1000.0; cum=0; halt=False
            for t in xs:
                if halt: continue
                out.append(t); cum += num(t.get("net_pnl")) or 0
                if cum <= -frac*start: halt=True
        return out

    overlays = {"all": stat(trades), "max_1_open": selected_summary(max_concurrent(1)), "max_2_open": selected_summary(max_concurrent(2))}
    for m in (5,10,15,30): overlays[f"cooldown_{m}m"] = selected_summary(cooldown(m))
    for n in (2,3,4): overlays[f"halt_after_{n}_losses_rest_of_day"] = selected_summary(halt_after_losses(n))
    for f in (.05,.10,.15): overlays[f"daily_loss_limit_{int(f*100)}pct"] = selected_summary(loss_limit(f))

    overlay_sets = {"max_1_open": max_concurrent(1), "max_2_open": max_concurrent(2)}
    for m in (10,15,30): overlay_sets[f"cooldown_{m}m"] = cooldown(m)
    overlay_daily = {}
    for name, selected in overlay_sets.items():
        overlay_daily[name] = {}
        for day in sorted(set(t["decision_date"] for t in trades)):
            overlay_daily[name][day] = stat([x for x in selected if x["decision_date"] == day])

    cluster_rows=[]
    for day in sorted(set(t["decision_date"] for t in trades)):
        xs=[x for x in trades if x["decision_date"]==day]
        cluster_id=0; last=None; rank=0
        for t in xs:
            now=dt(t["entry_time"])
            if last is None or (now-last).total_seconds()>15*60:
                cluster_id += 1; rank=1
            else:
                rank += 1
            r=dict(t); r["cluster_id"]=f"{day}:{cluster_id}"; r["cluster_rank"]=rank; cluster_rows.append(r); last=now
    clusters={
        "first_signal": stat([x for x in cluster_rows if x["cluster_rank"]==1]),
        "repeated_within_15m": stat([x for x in cluster_rows if x["cluster_rank"]>1]),
        "cluster_count": len(set(x["cluster_id"] for x in cluster_rows)),
    }

    # Health-feature predictive diagnostics: state before each trade vs next trade outcome.
    flagged = defaultdict(lambda: {"on": [], "off": []})
    health_rows=[]
    for day in sorted(set(t["decision_date"] for t in trades)):
        xs=[x for x in trades if x["decision_date"]==day]
        prev=[]; realized=0.0; start=num(xs[0].get("cash_before")) or 1000.0; peak=start; loss_streak=0
        for t in xs:
            equity=start+realized; peak=max(peak,equity); dd=(peak-equity)/peak if peak else 0
            wins5=[1 if (num(x.get("net_pnl")) or 0)>0 else 0 for x in prev[-5:]]
            flags={
                "daily_drawdown_5pct": dd>=.05,
                "daily_drawdown_10pct": dd>=.10,
                "daily_drawdown_15pct": dd>=.15,
                "loss_streak_2": loss_streak>=2,
                "loss_streak_4": loss_streak>=4,
                "rolling5_winrate_below_40pct": len(wins5)>=5 and avg(wins5)<.40,
                "rolling5_winrate_below_20pct": len(wins5)>=5 and avg(wins5)<=.20,
                "risk_off_regime": str(t.get("regime")).startswith("RISK_OFF") or t.get("regime")=="REVERSAL_DOWN",
                "vix_up_5pct": (t.get("vix_change_pct") or 0)>=.05,
            }
            if len(prev)>=6:
                old=prev[-6:-3]; recent=prev[-3:]
                old_w=avg([1 if (num(x.get("net_pnl")) or 0)>0 else 0 for x in old]); new_w=avg([1 if (num(x.get("net_pnl")) or 0)>0 else 0 for x in recent])
                old_mfe=med([num(x.get("mfe")) for x in old]); new_mfe=med([num(x.get("mfe")) for x in recent])
                old_mae=med([abs(num(x.get("mae")) or 0) for x in old]); new_mae=med([abs(num(x.get("mae")) or 0) for x in recent])
                flags["winrate_degraded_33pp"] = old_w is not None and new_w is not None and new_w <= old_w - .333
                flags["mfe_decreasing_30pct"] = old_mfe is not None and old_mfe>0 and new_mfe is not None and new_mfe < .70*old_mfe
                flags["mae_worsening_30pct"] = old_mae is not None and old_mae>0 and new_mae is not None and new_mae > 1.30*old_mae
            else:
                flags.update({"winrate_degraded_33pp":False,"mfe_decreasing_30pct":False,"mae_worsening_30pct":False})
            health_rows.append({"signal_id":t.get("signal_id"),"day":day,"time":t.get("entry_time"),"flags":[k for k,v in flags.items() if v],"pnl":t.get("net_pnl"),"exit_reason":t.get("exit_reason")})
            for k,v in flags.items(): flagged[k]["on" if v else "off"].append(t)
            realized += num(t.get("net_pnl")) or 0
            if (num(t.get("net_pnl")) or 0)<0: loss_streak += 1
            else: loss_streak=0
            prev.append(t)
    health_effects={k:{"flag_on":stat(v["on"]),"flag_off":stat(v["off"])} for k,v in flagged.items()}

    # Contract selection quality.
    def bucket(v, edges, labels):
        if v is None: return "UNKNOWN"
        for e,l in zip(edges,labels):
            if v<e: return l
        return labels[-1]
    contract_rows=[]
    for t in trades:
        s=((t.get("selection") or {}).get("selected") or {})
        ask=num(s.get("ask") or t.get("entry_ask")); bid=num(s.get("bid") or t.get("entry_bid"))
        delta=abs(num(s.get("delta")) or 0) if num(s.get("delta")) is not None else None
        dte=num(s.get("dte")); spread=num(s.get("spread_pct")); premium=ask*100 if ask is not None else None
        r=dict(t); r.update({"delta":delta,"dte":dte,"spread":spread,"premium":premium})
        contract_rows.append(r)
    dimensions={
        "delta":{"0.25-0.35":lambda r:r["delta"] is not None and .25<=r["delta"]<.35,"0.35-0.45":lambda r:r["delta"] is not None and .35<=r["delta"]<.45,"0.45-0.55":lambda r:r["delta"] is not None and .45<=r["delta"]<.55,"0.55-0.75":lambda r:r["delta"] is not None and .55<=r["delta"]<=.75},
        "dte":{"1":lambda r:r["dte"]==1,"2-3":lambda r:r["dte"] is not None and 2<=r["dte"]<=3,"4+":lambda r:r["dte"] is not None and r["dte"]>=4},
        "spread":{"<=1%":lambda r:r["spread"] is not None and r["spread"]<=.01,"1-3%":lambda r:r["spread"] is not None and .01<r["spread"]<=.03,"3-6%":lambda r:r["spread"] is not None and .03<r["spread"]<=.06,">6%":lambda r:r["spread"] is not None and r["spread"]>.06},
        "premium":{"<$200":lambda r:r["premium"] is not None and r["premium"]<200,"$200-300":lambda r:r["premium"] is not None and 200<=r["premium"]<300,"$300-400":lambda r:r["premium"] is not None and 300<=r["premium"]<400,"$400+":lambda r:r["premium"] is not None and r["premium"]>=400},
    }
    contract_analysis={d:{name:stat([r for r in contract_rows if fn(r)]) for name,fn in bins.items()} for d,bins in dimensions.items()}

    # Variable TP/SL using frozen tracker outcomes matched to live H01 signals.
    matched=[t["tracker"] for t in trades if t.get("tracker")]
    tp_sl={}
    for tp,sl in ((10,10),(10,20),(20,10),(20,20)):
        tp_sl[f"TP{tp}_SL{sl}"]=path_stat(matched,"call",60,tp,sl)

    guarded=None
    gp=ART / "GUARDED_SHADOW_V01.json"
    if gp.exists(): guarded=json.loads(gp.read_text()).get("summary")
    return {"trades":len(trades),"daily":by_day,"by_regime":by_regime,"overlap":overlap,"risk_overlays":overlays,
            "risk_overlay_by_day":overlay_daily,"correlated_signal_clusters_15m":clusters,
            "health_feature_effects":health_effects,"health_rows":health_rows,"contract_selection":contract_analysis,
            "tp_sl_matrix_60m":tp_sl,"guarded_shadow_summary":guarded}


def h09_analysis():
    p=ART/"H09_PUT_FLOW_PROSPECTIVE_V01.json"
    if not p.exists(): return {}
    d=json.loads(p.read_text())
    out={}
    for part in ("discovery","prospective"):
        rows=(d.get(part) or {}).get("rows") or []
        a=[r for r in rows if r.get("candidate_id")=="H09A_PUT_FLOW_MIRROR_V01"]
        cats=defaultdict(list)
        for r in a:
            riskoff=all((num(r.get(k)) or 0)<0 for k in ("spy_from_open","qqq_from_open","iwm_from_open"))
            cats["H09B_RISKOFF_CONFIRMED" if riskoff else "H09A_ONLY"].append(r)
        sec={}
        for name,xs in cats.items():
            sec[name]={}
            for h in (15,30,60):
                sec[name][str(h)]={
                    **stat(xs,ret_key=f"put_ret_{h}m",pnl_key="__none",mfe_key=f"put_mfe_{h}m",mae_key=f"put_mae_{h}m"),
                    "tp_sl":path_stat(xs,"put",h,10,10),
                }
            buckets=defaultdict(list)
            for r in xs:
                hour=dt(r["captured_at_utc"]).astimezone(NY).hour
                b="09:30-11" if hour<11 else "11-14" if hour<14 else "14-16"
                buckets[b].append(r)
            sec[name]["by_time_et"]={b:stat(v,ret_key="put_ret_30m",pnl_key="__none",mfe_key="put_mfe_30m",mae_key="put_mae_30m") for b,v in buckets.items()}
        out[part]={"episodes":len(a),"contexts":sec}
    out["interpretation_test"]="If H09A_ONLY is stronger at 15/30m while H09B-confirmed is stronger at 60m, tactical-vs-trend specialization is supported. Descriptive only."
    return out


def build_multi_episodes():
    cfg=json.loads(MULTI_CFG.read_text())
    raw=list(csv.DictReader(MULTI_DATA.open(encoding="utf-8")))
    groups=defaultdict(list)
    for r in raw:
        if r.get("symbol") in cfg["symbols"]: groups[(r["market_date"],r["symbol"])].append(r)
    market_first=defaultdict(dict)
    for (day,sym),items in groups.items():
        if sym in {"SPY","QQQ","IWM"} and items:
            first=min(items,key=lambda x:x["captured_at_utc"]); market_first[day][sym]=num(first.get("spot"))
    episodes=[]
    for (day,sym),items in sorted(groups.items()):
        items.sort(key=lambda x:x["captured_at_utc"]); first_spot=num(items[0].get("spot")); history=[]; last={}
        for base in items:
            row=derive_row(base,first_spot,history,market_first.get(day))
            for cand in active_candidates(cfg,row):
                key=signal_key(cand["id"],sym)
                if not is_new_episode(last.get(key),row["captured_at_utc"],cfg["episode_gap_minutes"]): continue
                last[key]=row["captured_at_utc"]
                rec=dict(row); rec["candidate_id"]=cand["id"]; rec["candidate_side"]=cand["side"]
                rec["partition"]="DISCOVERY" if day<=cfg["discovery_cutoff"] else "PROSPECTIVE"
                episodes.append(rec)
            history.append({"captured_at_utc":row["captured_at_utc"],"spot":row["spot"]}); history=history[-8:]
    return cfg,episodes


def multi_analysis():
    cfg,episodes=build_multi_episodes()
    # Candidate/ticker stability.
    ticker={}
    for cand in cfg["candidates"]:
        cid=cand["id"]; side=cand["side"].lower(); ticker[cid]={}
        for sym in cfg["symbols"]:
            xs=[r for r in episodes if r["candidate_id"]==cid and r["symbol"]==sym]
            if not xs: continue
            days=defaultdict(list)
            for r in xs: days[r["market_date"]].append(r)
            day_means=[]
            for day,rs in days.items():
                vals=[num(x.get(f"{side}_terminal_return_30m")) for x in rs]; vals=[x for x in vals if x is not None]
                if vals: day_means.append(avg(vals))
            ticker[cid][sym]={
                "30m":stat(xs,ret_key=f"{side}_terminal_return_30m",pnl_key="__none",mfe_key=f"{side}_best_return_30m",mae_key=f"{side}_worst_return_30m"),
                "60m":stat(xs,ret_key=f"{side}_terminal_return_60m",pnl_key="__none",mfe_key=f"{side}_best_return_60m",mae_key=f"{side}_worst_return_60m"),
                "tp10_sl10_30m":path_stat(xs,side,30,10,10),
                "days":len(day_means),"positive_day_fraction":sum(x>0 for x in day_means)/len(day_means) if day_means else None,
            }
    # Aggregate duplicate families into one opportunity per timestamp/symbol/side.
    opps={}
    for r in episodes:
        k=(r["market_date"],r["captured_at_utc"],r["symbol"],r["candidate_side"])
        o=opps.setdefault(k,{"day":r["market_date"],"time":r["captured_at_utc"],"symbol":r["symbol"],"side":r["candidate_side"],"candidate_ids":[],"row":r})
        o["candidate_ids"].append(r["candidate_id"])
    opportunities=[]
    for o in opps.values():
        o["candidate_ids"]=sorted(set(o["candidate_ids"])); o["support_count"]=len(o["candidate_ids"])
        r=o["row"]; side=o["side"].lower()
        o["ret30"]=num(r.get(f"{side}_terminal_return_30m")); o["ret60"]=num(r.get(f"{side}_terminal_return_60m"))
        o["mfe30"]=num(r.get(f"{side}_best_return_30m")); o["mae30"]=num(r.get(f"{side}_worst_return_30m"))
        o["path30"]=r.get(f"{side}_30m_tp10_sl10")
        gvals=[r.get("market_spy_from_first"),r.get("market_qqq_from_first"),r.get("market_iwm_from_first")]
        o["global_regime"]=regime_from_values(*gvals,r.get("vix_change_pct"))
        own=num(r.get("own_from_first")); local_side="CALL" if own is not None and own>0 else "PUT" if own is not None and own<0 else "FLAT"
        global_side="CALL" if str(o["global_regime"]).startswith("RISK_ON") else "PUT" if str(o["global_regime"]).startswith("RISK_OFF") else "NONE"
        if local_side==o["side"] and global_side==o["side"]: align="GLOBAL_LOCAL_ALIGNED"
        elif local_side==o["side"] and global_side not in {o["side"],"NONE"}: align="LOCAL_DIVERGENCE"
        elif local_side==o["side"]: align="LOCAL_ONLY"
        elif global_side==o["side"]: align="GLOBAL_ONLY"
        else: align="MIXED_OR_COUNTER"
        o["alignment"]=align
        ask=num(r.get(f"entry_{side}_ask")); bid=num(r.get(f"entry_{side}_bid")); delta=num(r.get(f"entry_{side}_delta")); dte=num(r.get(f"entry_{side}_dte"))
        o["premium_cost"]=ask*100 if ask is not None else None
        o["entry_delta"]=delta; o["entry_dte"]=dte
        o["entry_spread_pct"]=(ask-bid)/ask if ask and bid is not None else None
        opportunities.append(o)

    support={str(k):stat([o for o in opportunities if o["support_count"]==k],ret_key="ret30",pnl_key="__none",mfe_key="mfe30",mae_key="mae30") for k in sorted(set(o["support_count"] for o in opportunities))}
    combos=defaultdict(list)
    for o in opportunities: combos[" + ".join(o["candidate_ids"])].append(o)
    combo_stats={k:stat(v,ret_key="ret30",pnl_key="__none",mfe_key="mfe30",mae_key="mae30") for k,v in combos.items()}
    alignment={k:stat([o for o in opportunities if o["alignment"]==k],ret_key="ret30",pnl_key="__none",mfe_key="mfe30",mae_key="mae30") for k in sorted(set(o["alignment"] for o in opportunities))}

    # Opposite-side conflicts within exact/2m/5m windows.
    conflicts={}
    for window in (0,2,5):
        pairs=[]
        by_ds=defaultdict(list)
        for o in opportunities: by_ds[(o["day"],o["symbol"])].append(o)
        for key,items in by_ds.items():
            items=sorted(items,key=lambda x:x["time"])
            for i,a in enumerate(items):
                ta=dt(a["time"])
                for b in items[i+1:]:
                    delta=(dt(b["time"])-ta).total_seconds()/60
                    if delta>window and window>0: break
                    if window==0 and delta!=0: break
                    if a["side"]!=b["side"] and delta<=window:
                        pairs.append({"day":a["day"],"symbol":a["symbol"],"minutes_apart":delta,"a_side":a["side"],"a_ret30":a["ret30"],"b_side":b["side"],"b_ret30":b["ret30"]})
        conflicts[f"within_{window}m"]={"n":len(pairs),"rows":pairs[:100]}

    # Executability by simple premium budgets; signal quality remains separate.
    executable={}
    for budget in (200,400,500,1000):
        xs=[o for o in opportunities if o["premium_cost"] is not None]
        yes=[o for o in xs if o["premium_cost"]<=budget]
        executable[str(budget)]={"known":len(xs),"executable":len(yes),"rate":len(yes)/len(xs) if xs else None,
                                  "quality_if_executable":stat(yes,ret_key="ret30",pnl_key="__none",mfe_key="mfe30",mae_key="mae30")}
    exec_ticker={}
    for sym in cfg["symbols"]:
        xs=[o for o in opportunities if o["symbol"]==sym and o["premium_cost"] is not None]
        if not xs: continue
        exec_ticker[sym]={"n":len(xs),"median_premium":med([o["premium_cost"] for o in xs]),"median_spread_pct":med([o["entry_spread_pct"] for o in xs]),
                          "pct_under_400":sum(o["premium_cost"]<=400 for o in xs)/len(xs)}

    # TP/SL family comparison, descriptive only.
    tp_sl={}
    for cand in cfg["candidates"]:
        cid=cand["id"]; side=cand["side"].lower(); xs=[r for r in episodes if r["candidate_id"]==cid]
        tp_sl[cid]={}
        for tp,sl in ((10,10),(10,20),(20,10),(20,20)):
            tp_sl[cid][f"TP{tp}_SL{sl}"]=path_stat(xs,side,60,tp,sl)

    # By global regime and local/global alignment.
    regime_stats={k:stat([o for o in opportunities if o["global_regime"]==k],ret_key="ret30",pnl_key="__none",mfe_key="mfe30",mae_key="mae30") for k in sorted(set(o["global_regime"] for o in opportunities))}
    candidate_regime={}
    for cand in cfg["candidates"]:
        cid=cand["id"]; side=cand["side"].lower(); candidate_regime[cid]={}
        selected=[r for r in episodes if r["candidate_id"]==cid]
        for r in selected:
            r["_research_regime"]=regime_from_values(r.get("market_spy_from_first"),r.get("market_qqq_from_first"),r.get("market_iwm_from_first"),r.get("vix_change_pct"))
        for rg in sorted(set(r.get("_research_regime") for r in selected)):
            xs=[r for r in selected if r.get("_research_regime")==rg]
            candidate_regime[cid][rg]={"30m":stat(xs,ret_key=f"{side}_terminal_return_30m",pnl_key="__none",mfe_key=f"{side}_best_return_30m",mae_key=f"{side}_worst_return_30m"),
                                       "60m":stat(xs,ret_key=f"{side}_terminal_return_60m",pnl_key="__none",mfe_key=f"{side}_best_return_60m",mae_key=f"{side}_worst_return_60m")}

    by_partition={}
    for part in ("DISCOVERY","PROSPECTIVE"):
        ops=[o for o in opportunities if o["row"].get("partition")==part]
        psec={"opportunities":len(ops),"support_count":{},"ticker_candidate":{}}
        for k in sorted(set(o["support_count"] for o in ops)):
            psec["support_count"][str(k)]=stat([o for o in ops if o["support_count"]==k],ret_key="ret30",pnl_key="__none",mfe_key="mfe30",mae_key="mae30")
        for cand in cfg["candidates"]:
            cid=cand["id"]; side=cand["side"].lower(); psec["ticker_candidate"][cid]={}
            for sym in cfg["symbols"]:
                xs=[r for r in episodes if r.get("partition")==part and r["candidate_id"]==cid and r["symbol"]==sym]
                if xs:
                    psec["ticker_candidate"][cid][sym]={"30m":stat(xs,ret_key=f"{side}_terminal_return_30m",pnl_key="__none",mfe_key=f"{side}_best_return_30m",mae_key=f"{side}_worst_return_30m"),
                                                              "60m":stat(xs,ret_key=f"{side}_terminal_return_60m",pnl_key="__none",mfe_key=f"{side}_best_return_60m",mae_key=f"{side}_worst_return_60m")}
        by_partition[part]=psec

    return {"episodes":len(episodes),"opportunities":len(opportunities),"ticker_specialization":ticker,"support_count":support,"support_combinations":combo_stats,
            "by_partition":by_partition,"global_local_alignment":alignment,"by_global_regime":regime_stats,"candidate_by_regime":candidate_regime,"conflicts":conflicts,"executability":executable,"executability_by_ticker":exec_ticker,
            "tp_sl_matrix_60m":tp_sl,"opportunity_rows":opportunities}


def fetch_jev_days(days):
    out={}
    for day in sorted(days):
        try:
            with urlopen(f"http://127.0.0.1:8787/api/results?day={day}&limit=5000&offset=0",timeout=4) as r:
                data=json.load(r); out[day]=data.get("rows") or []
        except Exception:
            out[day]=[]
    return out


def jev_analysis(multi):
    # Existing calibration report + directional confluence with Multi opportunities, including SKIP decisions.
    cal_path=Path("/home/ljamtz/jev-lab/data/calibration-analysis.json")
    cal={}
    if cal_path.exists():
        d=json.loads(cal_path.read_text()); diag=d.get("diagnostics") or {}
        bands=defaultdict(lambda:{"n":0,"wins":0})
        for seg in d.get("segments") or []:
            for b in seg.get("confidence_bands_descriptive_only") or []:
                key=f"{b.get('low'):.2f}-{b.get('high'):.2f}"
                bands[key]["n"] += int(b.get("n") or 0); bands[key]["wins"] += int(b.get("wins") or 0)
        cal={"status":d.get("status"),"session_days":diag.get("session_days"),"decisions":diag.get("decisions"),"qualified_directional_decisions":diag.get("qualified_directional_decisions"),
             "maximum_directional_confidence":diag.get("maximum_directional_confidence"),"closed_profit_labels":diag.get("closed_profit_labels"),
             "bands_aggregated_descriptive":{k:{**v,"win_rate":v["wins"]/v["n"] if v["n"] else None} for k,v in bands.items()}}
    opps=multi.get("opportunity_rows") or []
    days=set(o["day"] for o in opps)
    jev=fetch_jev_days(days)
    by_key=defaultdict(list)
    for day,rows in jev.items():
        for r in rows:
            try: ts=dt(r.get("timestamp")).timestamp()
            except Exception: continue
            by_key[(day,r.get("symbol"))].append((ts,r))
    for k in by_key: by_key[k].sort(key=lambda x:x[0])
    matched=[]
    for o in opps:
        arr=by_key.get((o["day"],o["symbol"])) or []
        if not arr: continue
        target=dt(o["time"]).timestamp(); times=[x[0] for x in arr]; i=bisect.bisect_left(times,target); cand=[]
        if i<len(arr): cand.append((abs(arr[i][0]-target),arr[i][1]))
        if i: cand.append((abs(arr[i-1][0]-target),arr[i-1][1]))
        if not cand: continue
        gap,j=min(cand,key=lambda x:x[0])
        if gap>90: continue
        js=str(j.get("side") or "NO_TRADE").upper(); oside=o["side"]
        relation="AGREE" if js==oside else "OPPOSITE" if js in {"CALL","PUT"} and js!=oside else "JEV_NO_TRADE"
        matched.append({"relation":relation,"confidence":num(j.get("confidence")),"jev_side":js,"options_side":oside,"ret30":o.get("ret30"),"ret60":o.get("ret60"),"symbol":o["symbol"],"status":j.get("status"),"gap_seconds":gap})
    relation={k:stat([x for x in matched if x["relation"]==k],ret_key="ret30",pnl_key="__none",mfe_key="__none",mae_key="__none") for k in ("AGREE","OPPOSITE","JEV_NO_TRADE")}
    confidence={}
    bins=[(0,.55,"<55%"),(.55,.60,"55-60%"),(.60,.65,"60-65%"),(.65,1.01,">=65%")]
    for lo,hi,label in bins:
        xs=[x for x in matched if x["confidence"] is not None and lo<=x["confidence"]<hi]
        confidence[label]=stat(xs,ret_key="ret30",pnl_key="__none",mfe_key="__none",mae_key="__none")
    return {"calibration":cal,"matched_options_opportunities":len(matched),"options_outcome_by_jev_relation":relation,"by_jev_confidence":confidence,
            "note":"Jev relation uses internal CALL/PUT/NO_TRADE direction even when status=SKIP; descriptive filter research only."}


def router_blueprint():
    return {
        "mode":"RESEARCH_BLUEPRINT_ONLY","auto_apply":False,"broker_orders_enabled":False,
        "stages":[
            "GLOBAL_REGIME: RISK_ON/RISK_OFF/REVERSAL/CHOP",
            "LOCAL_TICKER_REGIME: own trend + relative strength/weakness",
            "STRATEGY_CANDIDATES: H01/H09/MS01-MS04",
            "SIGNAL_ARBITRATION: deduplicate, support_count, conflicts",
            "JEV_FILTER: agree/opposite/no-trade + confidence calibration",
            "STRATEGY_HEALTH: drawdown/loss-streak/winrate/MFE/MAE degradation",
            "EXECUTION_GATE: contract premium/delta/DTE/spread/liquidity",
            "RISK_OVERLAY: max concurrent, cooldown, daily loss limit, Guarded",
            "ALPACA_PAPER: only after prospective promotion",
        ],
        "promotion_principle":"A strategy/ticker/regime combination must survive prospective sessions, execution quality, and risk overlay before broker promotion.",
    }


def main():
    _,tracker_index=load_tracker()
    h01=h01_analysis(tracker_index)
    h09=h09_analysis()
    multi=multi_analysis()
    jev=jev_analysis(multi)
    # Keep report compact; raw opportunity rows are an internal join surface, not dashboard payload.
    multi.pop("opportunity_rows",None)
    result={
        "version":"SYSTEM_RESEARCH_DIAGNOSTICS_V01",
        "generated_at_utc":datetime.now(timezone.utc).isoformat(),
        "mode":"COUNTERFACTUAL_AND_SHADOW_RESEARCH_ONLY",
        "scientific_evidence":False,
        "auto_apply":False,
        "frozen_strategies_unchanged":True,
        "broker_orders_enabled":False,
        "warnings":[
            "Discovery and counterfactual results must not be promoted from the same sample used to discover them.",
            "H01 historical path resolution is approximately 1 minute; 15s/30s checkpoints are only available prospectively after telemetry is enabled.",
            "Risk overlay comparisons reuse observed trade outcomes and do not model all capital-interaction effects.",
        ],
        "h01":h01,
        "h09":h09,
        "multi_symbol":multi,
        "jev":jev,
        "future_system_router":router_blueprint(),
    }
    OUT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({
        "output":str(OUT),"h01_trades":h01.get("trades"),"multi_episodes":multi.get("episodes"),"multi_opportunities":multi.get("opportunities"),
        "jev_matches":jev.get("matched_options_opportunities"),"h09_prospective":(h09.get("prospective") or {}).get("episodes")
    },indent=2))


if __name__ == "__main__":
    main()
