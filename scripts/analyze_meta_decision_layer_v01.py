#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from options_system.meta_decision_layer import (
    annotate_episode_metrics,
    decision_from_reasons,
    dt,
    market_regime,
    multi_correlation_exposure,
    num,
    partition,
    summarize,
)

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts/intraday"
CFG = ROOT / "config/meta_decision_layer_v01.json"
OUT = ART / "META_DECISION_LAYER_V01.json"


def load(path: Path, default=None):
    if not path.exists():
        return {} if default is None else default
    return json.loads(path.read_text())


def build_h01(cfg, health, paper):
    health_map = {r.get("signal_id"): r for r in health}
    rows = []
    for trade in paper.get("live_ledger", []):
        if trade.get("hypothesis") != "CALL_FLOW_REVERSAL_V01":
            continue
        h = health_map.get(trade.get("signal_id"), {})
        capital = num(trade.get("capital_required"))
        pnl = num(trade.get("net_pnl"))
        exec_gate = trade.get("execution_gate") or {}
        selection = trade.get("selection") or {}
        rows.append({
            "source": "H01",
            "strategy": "CALL_FLOW_REVERSAL_V01",
            "signal_id": trade.get("signal_id"),
            "day": trade.get("decision_date"),
            "time": trade.get("signal_time"),
            "symbol": "SPY",
            "side": "CALL",
            "contract": trade.get("contract"),
            "flags": h.get("flags") or [],
            "executable": bool(exec_gate.get("executable", selection.get("status") == "PASS")),
            "outcome_return": pnl / capital if pnl is not None and capital else None,
            "outcome_pnl": pnl,
            "exit_reason": trade.get("exit_reason"),
            "evidence_partition": partition(str(trade.get("decision_date")), cfg["discovery_cutoff"]),
        })
    annotate_episode_metrics(rows, cfg["episode_window_minutes"], cfg["flicker_window_minutes"])
    for row in rows:
        block, wait = [], []
        if not row["executable"]:
            block.append("EXECUTION_CONTRACT_FAIL")
        flags = set(row.get("flags") or [])
        for flag in cfg["h01"]["health_block_flags"]:
            if flag in flags:
                block.append(f"HEALTH:{flag}")
        for flag in cfg["h01"]["regime_block_flags"]:
            if flag in flags:
                block.append(f"REGIME:{flag}")
        if row.get("is_episode_repeat"):
            wait.append("CORRELATED_REPEAT_WITHIN_15M")
        row["block_reasons"] = block
        row["wait_reasons"] = wait
        row["decision"] = decision_from_reasons(block, wait)
    return rows


def build_h09(cfg, h09):
    grouped = defaultdict(list)
    for part in ("discovery", "prospective"):
        for row in (h09.get(part) or {}).get("rows", []):
            grouped[row.get("captured_at_utc")].append(row)
    rows = []
    for stamp, variants in grouped.items():
        ids = {r.get("candidate_id") for r in variants}
        is_b = "H09B_PUT_FLOW_MIRROR_RISKOFF_V01" in ids
        raw = next((r for r in variants if r.get("candidate_id") == "H09B_PUT_FLOW_MIRROR_RISKOFF_V01"), variants[0])
        ask, bid = num(raw.get("put_entry_ask")), num(raw.get("put_entry_bid"))
        spread = (ask - bid) / ask if ask and bid is not None and ask > 0 else None
        regime = market_regime(raw.get("spy_from_open"), raw.get("qqq_from_open"), raw.get("iwm_from_open"))
        block, wait = [], []
        if not raw.get("put_contract") or ask is None or ask <= 0 or ask > cfg["h09"]["max_contract_price"]:
            block.append("EXECUTION:CONTRACT_OR_PRICE")
        if spread is not None and spread > cfg["h09"]["max_spread_pct"]:
            block.append("EXECUTION:SPREAD")
        if is_b and regime != "RISK_OFF":
            block.append("REGIME:H09B_NOT_RISK_OFF")
        if not is_b:
            wait.append("REGIME:WAIT_FOR_RISK_OFF_CONFIRMATION")
        rows.append({
            "source": "H09",
            "strategy": "H09B_PUT_FLOW_MIRROR_RISKOFF_V01" if is_b else "H09A_PUT_FLOW_MIRROR_V01",
            "candidate_ids": sorted(ids),
            "day": raw.get("decision_date"),
            "time": stamp,
            "symbol": "SPY",
            "side": "PUT",
            "contract": raw.get("put_contract"),
            "entry_ask": ask,
            "spread_pct": spread,
            "market_regime": regime,
            "executable": not any(x.startswith("EXECUTION") for x in block),
            "outcome_return": num(raw.get("put_ret_30m")),
            "outcome_tp_sl": raw.get("put_30m_tp10_sl10"),
            "evidence_partition": partition(str(raw.get("decision_date")), cfg["discovery_cutoff"]),
            "block_reasons": block,
            "wait_reasons": wait,
            "decision": decision_from_reasons(block, wait),
        })
    annotate_episode_metrics(rows, cfg["episode_window_minutes"], cfg["flicker_window_minutes"])
    return rows


def build_multi(cfg, arbitration, prospective):
    raw_index = defaultdict(list)
    for raw in prospective.get("rows", []):
        raw_index[(raw.get("captured_at_utc"), raw.get("symbol"))].append(raw)
    rows = []
    for opp in arbitration.get("rows", []):
        raw_candidates = raw_index.get((opp.get("time"), opp.get("symbol")), [])
        raw = next((r for r in raw_candidates if r.get("candidate_id") in set(opp.get("candidate_ids") or [])), None)
        if raw is None:
            continue
        side = str(opp.get("side") or "").upper()
        prefix = "call" if side == "CALL" else "put"
        ask = num(raw.get(f"entry_{prefix}_ask"))
        spread_proxy = num(raw.get("median_spread_pct_1pct"))
        regime = market_regime(raw.get("market_spy_from_first"), raw.get("market_qqq_from_first"), raw.get("market_iwm_from_first"))
        desired = "RISK_ON" if side == "CALL" else "RISK_OFF"
        block, wait = [], []
        if not raw.get(f"entry_{prefix}_contract") or ask is None or ask <= 0 or ask > cfg["multi"]["max_contract_price"]:
            block.append("EXECUTION:CONTRACT_OR_PRICE")
        if spread_proxy is not None and spread_proxy > cfg["multi"]["max_market_spread_pct"]:
            block.append("EXECUTION:MARKET_SPREAD_PROXY")
        if cfg["multi"]["require_all3_regime_alignment"] and regime != desired:
            block.append(f"REGIME:REQUIRE_{desired}")
        if int(opp.get("support_count") or 0) >= cfg["multi"]["redundant_support_count_ge"]:
            wait.append("REDUNDANT_SUPPORT_NOT_CONFIRMATION")
        rows.append({
            "source": "MULTI",
            "strategy": "+".join(opp.get("candidate_ids") or []),
            "candidate_ids": opp.get("candidate_ids") or [],
            "support_count": opp.get("support_count"),
            "day": opp.get("day"),
            "time": opp.get("time"),
            "symbol": opp.get("symbol"),
            "side": side,
            "contract": raw.get(f"entry_{prefix}_contract"),
            "entry_ask": ask,
            "delta": num(raw.get(f"entry_{prefix}_delta")),
            "dte": num(raw.get(f"entry_{prefix}_dte")),
            "market_spread_proxy": spread_proxy,
            "market_regime": regime,
            "executable": not any(x.startswith("EXECUTION") for x in block),
            "outcome_return": num(raw.get(f"{prefix}_terminal_return_30m")),
            "outcome_tp_sl": raw.get(f"{prefix}_30m_tp10_sl10"),
            "evidence_partition": partition(str(opp.get("day")), cfg["discovery_cutoff"]),
            "block_reasons": block,
            "wait_reasons": wait,
            "decision": decision_from_reasons(block, wait),
        })
    annotate_episode_metrics(rows, cfg["episode_window_minutes"], cfg["flicker_window_minutes"])
    multi_correlation_exposure(rows)
    return rows


def main():
    cfg = load(CFG)
    system = load(ART / "SYSTEM_RESEARCH_DIAGNOSTICS_V01.json")
    paper = load(ART / "PAPER_TRADING_LIVE_STATE_V01.json")
    h09 = load(ART / "H09_PUT_FLOW_PROSPECTIVE_V01.json")
    arbitration = load(ART / "MULTISYMBOL_SIGNAL_ARBITRATION_V01.json")
    multi_prospective = load(ART / "MULTISYMBOL_PROSPECTIVE_V01.json")
    h01 = build_h01(cfg, (system.get("h01") or {}).get("health_rows") or [], paper)
    h09_rows = build_h09(cfg, h09)
    multi = build_multi(cfg, arbitration, multi_prospective)
    rows = sorted(h01 + h09_rows + multi, key=lambda r: (str(r.get("time")), r.get("source", "")))
    summary = {}
    for source in ("H01", "H09", "MULTI"):
        src = [r for r in rows if r.get("source") == source]
        summary[source] = {
            "all": summarize(src),
            "DISCOVERY": summarize([r for r in src if r.get("evidence_partition") == "DISCOVERY"]),
            "PROSPECTIVE": summarize([r for r in src if r.get("evidence_partition") == "PROSPECTIVE"]),
        }
    output = {
        "version": cfg["version"],
        "mode": cfg["mode"],
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "discovery_cutoff": cfg["discovery_cutoff"],
        "prospective_start_after": cfg["prospective_start_after"],
        "scientific_evidence": False,
        "auto_apply": False,
        "broker_orders_enabled": False,
        "decision_features_causal_only": True,
        "outcomes_used_for_decision": False,
        "policy": cfg,
        "summary": summary,
        "rows": rows,
        "warning": "v0.1 is shadow-only. Persistence, flickering and cross-symbol correlation are measured but not promoted to gates except the pre-frozen H01 15m repeat rule. Validate only sessions after 2026-10-15 prospectively.",
    }
    OUT.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps({"output": str(OUT), "rows": len(rows), "summary": summary}, indent=2))


if __name__ == "__main__":
    main()
