"""Baseline H02 activation audit from already-collected tracker (no broker calls)."""
from collections import defaultdict


def audit_h02(rows):
    from options_system.put_research_shadow import number
    by_day = defaultdict(lambda: {"snapshots": 0, "skew_pass": 0, "ratio_pass": 0,
                                 "both_pass": 0, "put_quote_present": 0, "h02_marked_active": 0})
    for row in rows:
        out = by_day[str(row.get("decision_date") or "UNKNOWN")]
        out["snapshots"] += 1
        skew, ratio = number(row.get("put_call_iv_skew")), number(row.get("put_call_volume_ratio_1pct"))
        sp = skew is not None and skew > 0.0045
        rp = ratio is not None and ratio < 1.05
        out["skew_pass"] += int(sp)
        out["ratio_pass"] += int(rp)
        out["both_pass"] += int(sp and rp)
        out["put_quote_present"] += int(bool(row.get("put_contract")) and number(row.get("put_entry_ask")) is not None)
        out["h02_marked_active"] += int("PUT_SKEW_SHORT_V01" in (row.get("active_hypotheses") or "").split(";"))
    return dict(sorted(by_day.items()))
