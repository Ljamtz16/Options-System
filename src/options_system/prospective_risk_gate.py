EVIDENCE_TIERS = (
    {"min_executed": 0, "min_decided": 0, "max_fraction": 0.20, "label": "BOOTSTRAP"},
    {"min_executed": 20, "min_decided": 20, "max_fraction": 0.40, "label": "EARLY"},
    {"min_executed": 50, "min_decided": 50, "max_fraction": 0.60, "label": "ESTABLISHED"},
    {"min_executed": 100, "min_decided": 100, "max_fraction": 0.80, "label": "MATURE"},
)

DEFAULT_MAX_STRESS_DRAWDOWN = 0.20
FRACTIONS = (0.20, 0.40, 0.60, 0.80)

def evidence_cap(executed_trades, decided_episodes):
    eligible = EVIDENCE_TIERS[0]
    for tier in EVIDENCE_TIERS:
        if executed_trades >= tier["min_executed"] and decided_episodes >= tier["min_decided"]:
            eligible = tier
    return {"max_fraction": eligible["max_fraction"], "tier": eligible["label"]}

def stress_cap(stress_report, max_drawdown=DEFAULT_MAX_STRESS_DRAWDOWN):
    scenarios = (stress_report or {}).get("scenarios", {})
    if not scenarios:
        return {"max_fraction": 0.20, "reason": "NO_STRESS_DATA", "worst_drawdown": None}
    allowed = []
    worst_by_fraction = {}
    for fraction in FRACTIONS:
        key = f"pct_{int(fraction*100)}"
        dds = [
            float(s["strategies"][key]["max_drawdown_pct"])
            for s in scenarios.values()
            if key in s.get("strategies", {})
        ]
        worst = max(dds) if dds else 1.0
        worst_by_fraction[fraction] = worst
        if worst <= max_drawdown:
            allowed.append(fraction)
    cap = max(allowed) if allowed else 0.0
    return {
        "max_fraction": cap,
        "reason": "WITHIN_STRESS_DRAWDOWN_LIMIT" if allowed else "NO_FRACTION_WITHIN_STRESS_LIMIT",
        "worst_drawdown": worst_by_fraction.get(cap) if cap else min(worst_by_fraction.values(), default=None),
        "worst_drawdown_by_fraction": {f"pct_{int(k*100)}": v for k,v in worst_by_fraction.items()},
    }

def build_risk_gate(prospective_report, stress_report, max_stress_drawdown=DEFAULT_MAX_STRESS_DRAWDOWN):
    episodes = prospective_report.get("prospective_episodes", [])
    ledger = prospective_report.get("virtual_account", {}).get("ledger", [])
    executed = sum(1 for x in ledger if x.get("execution_status") == "EXECUTED")
    # Compatibility: some ledgers use sizing_status; official one-contract ledger uses execution_status.
    if not executed:
        executed = sum(1 for x in ledger if x.get("sizing_status") == "EXECUTED")
    decided = sum(1 for e in episodes if e.get("tp_sl") in ("TP_FIRST", "SL_FIRST"))
    ev = evidence_cap(executed, decided)
    st = stress_cap(stress_report, max_stress_drawdown)
    allowed = min(ev["max_fraction"], st["max_fraction"])
    status = "BLOCKED" if allowed <= 0 else "ACTIVE"
    return {
        "version": "v0.1",
        "scientific_evidence": False,
        "purpose": "prospective_position_sizing_governance_only",
        "status": status,
        "allowed_max_fraction": allowed,
        "recommended_strategy": f"pct_{int(allowed*100)}" if allowed > 0 else "NO_TRADE",
        "evidence": {
            "executed_trades": executed,
            "decided_episodes": decided,
            "tier": ev["tier"],
            "max_fraction": ev["max_fraction"],
        },
        "stress": {
            **st,
            "max_allowed_drawdown": float(max_stress_drawdown),
        },
        "rules": {
            "no_leverage": True,
            "whole_contracts_only": True,
            "cannot_override_frozen_hypothesis": True,
            "diagnostic_history_does_not_unlock_sizing": True,
        },
    }
