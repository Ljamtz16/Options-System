#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import timedelta
from pathlib import Path

from options_system.h09_put_flow import is_new_episode as h09_new_episode
from options_system.intraday_episodes import group_episodes
from options_system.multisymbol_shadow import active_candidates, derive_row, is_new_episode as multi_new_episode, signal_key
from options_system.session_cache import snapshot_refs
from options_system.sl_first_recovery import analyze_episode, num, stamp, summarize

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts/intraday"
OUT = ART / "SL_FIRST_RECOVERY_STUDY_V01.json"
CFG = json.loads((ROOT / "config/sl_first_recovery_v01.json").read_text())


def h01_episodes():
    rows = list(csv.DictReader((ROOT / "data/processed/intraday/prospective_hypothesis_tracker_v02.csv").open()))
    marked = []
    for row in rows:
        x = dict(row)
        x["h01_active"] = "CALL_FLOW_REVERSAL_V01" in (row.get("active_hypotheses") or "").split(";")
        marked.append(x)
    out = []
    for ep in group_episodes(marked, "h01_active", 6):
        row = ep["rows"][0]
        ask = num(row.get("call_entry_ask"))
        contract = row.get("call_contract")
        if ask and contract:
            out.append({
                "strategy": "CALL_FLOW_REVERSAL_V01", "source": "H01", "evidence": "FROZEN_TRACKER",
                "dataset": "SPY", "day": row["decision_date"], "symbol": "SPY", "side": "CALL",
                "signal_time": stamp(row["captured_at_utc"]), "contract": contract, "initial_ask": ask,
                "horizon_minutes": 60,
            })
    return out


def h09_episodes():
    data = json.loads((ART / "H09_PUT_FLOW_PROSPECTIVE_V01.json").read_text())
    out = []
    wanted = {"H09A_PUT_FLOW_MIRROR_V01", "H09B_PUT_FLOW_MIRROR_RISKOFF_V01"}
    for part in ("discovery", "prospective"):
        for row in data.get(part, {}).get("rows") or []:
            strategy = row.get("candidate_id")
            ask = num(row.get("put_entry_ask"))
            contract = row.get("put_contract")
            if strategy in wanted and ask and contract:
                out.append({
                    "strategy": strategy, "source": "H09", "evidence": part.upper(),
                    "dataset": "SPY", "day": row["decision_date"], "symbol": "SPY", "side": "PUT",
                    "signal_time": stamp(row["captured_at_utc"]), "contract": contract, "initial_ask": ask,
                    "horizon_minutes": 60,
                })
    return out


def multi_episodes():
    cfg = json.loads((ROOT / "config/multisymbol_shadow_v01.json").read_text())
    wanted = {"MS01_PUT_BREAKDOWN_RISKOFF_V01", "MS03_PUT_RELATIVE_WEAKNESS_V01"}
    raw = list(csv.DictReader((ROOT / "data/processed/intraday/intraday_options_v2.csv").open()))
    groups = defaultdict(list)
    for row in raw:
        if row.get("symbol") in cfg["symbols"]:
            groups[(row["market_date"], row["symbol"])].append(row)
    market_first_by_day = defaultdict(dict)
    for (day, symbol), items in groups.items():
        if symbol in {"SPY", "QQQ", "IWM"} and items:
            first = min(items, key=lambda x: x["captured_at_utc"])
            market_first_by_day[day][symbol] = float(first["spot"])
    out = []
    last = {}
    for (day, symbol), rows in sorted(groups.items()):
        rows.sort(key=lambda x: x["captured_at_utc"])
        first_spot = float(rows[0]["spot"]) if rows and rows[0].get("spot") else None
        history = []
        for base in rows:
            row = derive_row(base, first_spot, history, market_first_by_day.get(day))
            for cand in active_candidates(cfg, row):
                if cand["id"] not in wanted:
                    continue
                key = f"{day}|{signal_key(cand['id'], symbol)}"
                if not multi_new_episode(last.get(key), row["captured_at_utc"], cfg["episode_gap_minutes"]):
                    continue
                last[key] = row["captured_at_utc"]
                pref = cand["side"].lower()
                ask = num(row.get(f"entry_{pref}_ask"))
                contract = row.get(f"entry_{pref}_contract")
                if ask and contract:
                    evidence = "DISCOVERY" if day <= cfg["discovery_cutoff"] else "PROSPECTIVE"
                    out.append({
                        "strategy": cand["id"], "source": "Multi-Symbol", "evidence": evidence,
                        "dataset": "MULTI", "day": day, "symbol": symbol, "side": cand["side"],
                        "signal_time": stamp(row["captured_at_utc"]), "contract": contract, "initial_ask": ask,
                        "horizon_minutes": 30,
                    })
            history.append({"captured_at_utc": row["captured_at_utc"], "spot": row["spot"]})
            history = history[-8:]
    return out


def quote_from_payload(payload, dataset, symbol, contract):
    try:
        if dataset == "SPY":
            snap = payload["options"]["snapshot"]["snapshots"][contract]
        else:
            snap = payload["symbols"][symbol]["option_snapshot"]["snapshots"][contract]
        q = snap.get("latestQuote") or {}
        bid, ask = num(q.get("bp")), num(q.get("ap"))
        if bid is None or bid <= 0:
            return None
        return {"bid": bid, "ask": ask}
    except (KeyError, TypeError):
        return None


def attach_paths(episodes):
    by_dataset_day = defaultdict(list)
    for ep in episodes:
        by_dataset_day[(ep["dataset"], ep["day"])].append(ep)
    results = []
    roots = {
        "SPY": (ROOT / "data/raw/prospective", "spy_options_*.json"),
        "MULTI": (ROOT / "data/raw/intraday", "intraday_options_*.json"),
    }
    refs_cache = {}
    for dataset in ("SPY", "MULTI"):
        root, pattern = roots[dataset]
        refs = snapshot_refs(root, pattern, skip_invalid=True)
        day_map = defaultdict(list)
        for ref in refs:
            day_map[ref.day].append(ref)
        refs_cache[dataset] = day_map
    for (dataset, day), day_eps in sorted(by_dataset_day.items()):
        paths = {id(ep): [] for ep in day_eps}
        refs = refs_cache[dataset].get(day, [])
        for ref in refs:
            t = stamp(ref.get("captured_at_utc"))
            active = [ep for ep in day_eps if ep["signal_time"] <= t <= ep["signal_time"] + timedelta(minutes=ep["horizon_minutes"])]
            if not active:
                continue
            payload = ref["payload"]
            for ep in active:
                q = quote_from_payload(payload, dataset, ep["symbol"], ep["contract"])
                if q:
                    paths[id(ep)].append({"time": t, **q})
        for ep in day_eps:
            results.append(analyze_episode(
                strategy=ep["strategy"], source=ep["source"], evidence=ep["evidence"],
                symbol=ep["symbol"], side=ep["side"], signal_time=ep["signal_time"],
                contract=ep["contract"], initial_ask=ep["initial_ask"],
                horizon_minutes=ep["horizon_minutes"], points=paths[id(ep)], config=CFG,
            ))
        print(f"SL_FIRST_DAY {dataset} {day} episodes={len(day_eps)} snapshots={len(refs)}", flush=True)
    return results


def main():
    episodes = h01_episodes() + h09_episodes() + multi_episodes()
    rows = attach_paths(episodes)
    by_strategy = {}
    by_strategy_evidence = {}
    for strategy in CFG["strategies"]:
        selected = [r for r in rows if r["strategy"] == strategy]
        by_strategy[strategy] = summarize(selected)
        evidences = sorted({r["evidence"] for r in selected})
        by_strategy_evidence[strategy] = {e: summarize([r for r in selected if r["evidence"] == e]) for e in evidences}
    report = {
        "version": CFG["version"], "mode": CFG["mode"],
        "generated_from": ["prospective_hypothesis_tracker_v02", "H09_PUT_FLOW_PROSPECTIVE_V01", "intraday_options_v2", "raw option snapshots"],
        "methodology": CFG["notes"], "config": CFG,
        "episode_count": len(rows), "evaluable_count": sum(bool(r.get("evaluable")) for r in rows),
        "by_strategy": by_strategy, "by_strategy_evidence": by_strategy_evidence,
        "episodes": rows,
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(OUT), "episodes": report["episode_count"], "evaluable": report["evaluable_count"], "by_strategy": by_strategy}, indent=2))


if __name__ == "__main__":
    main()
