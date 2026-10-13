#!/usr/bin/env python3

import csv
import json
from collections import defaultdict
from datetime import timedelta
from pathlib import Path

from options_system.put_research_shadow import (
    DEFAULTS,
    number,
    timestamp,
    _lookback,
    _return,
    _market_reason,
    _quote_reason,
)

ROOT = Path(__file__).resolve().parents[1]

DATA = ROOT / "data/processed/intraday/prospective_hypothesis_tracker_v02.csv"
BASE_CFG = ROOT / "config/put_research_shadow_v01.json"
V02_CFG = ROOT / "config/put_confirmation_shadow_v02.json"

OUT = ROOT / "artifacts/intraday/PUT_CONFIRM_SHADOW_V02_PROSPECTIVE.json"


def load_rows():
    with DATA.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    rows.sort(
        key=lambda r: (
            r.get("decision_date", ""),
            r.get("captured_at_utc", "")
        )
    )

    return rows


def reconstruct_h06(rows, cfg):
    seen = defaultdict(list)
    out = []

    for row in rows:
        day = str(row.get("decision_date") or "")
        now = timestamp(row)
        history = seen[day]

        spot = number(row.get("spot"))

        if spot is None or spot <= 0:
            history.append(row)
            continue

        prior15 = _lookback(history, now, 15)
        r5 = _return(history, now, spot, 5)

        sufficient = len(prior15) >= cfg["min_history_points"]

        reason = (
            _market_reason(row)
            or _quote_reason(row, cfg)
        )

        h06 = (
            sufficient
            and r5 is not None
            and r5 <= cfg["h06_max_5m_return"]
            and spot
            < min(prior15)
            * (
                1
                - cfg["h06_break_below_prior_low_fraction"]
            )
        )

        if h06 and reason is None:
            out.append({
                "decision_date": day,
                "captured_at_utc": row["captured_at_utc"],

                "spot": spot,

                "spy_from_open":
                    number(row.get("spy_from_open")),

                "qqq_from_open":
                    number(row.get("qqq_from_open")),

                "iwm_from_open":
                    number(row.get("iwm_from_open")),

                "contract":
                    row.get("put_contract"),

                "put_entry_ask":
                    number(row.get("put_entry_ask")),

                "put_entry_bid":
                    number(row.get("put_entry_bid")),

                "put_ret_15m":
                    number(row.get("put_ret_15m")),

                "put_15m_tp10_sl10":
                    row.get("put_15m_tp10_sl10")
            })

        history.append(row)

    return out


def evaluate_state_machine(activations, cfg):
    by_day = defaultdict(list)

    for a in activations:
        by_day[a["decision_date"]].append(a)

    signals = []

    min_minutes = cfg["state_machine"]["confirmation_min_minutes"]
    max_minutes = cfg["state_machine"]["confirmation_max_minutes"]
    lock_minutes = cfg["state_machine"]["post_signal_lock_minutes"]

    for day, rows in sorted(by_day.items()):
        rows.sort(key=timestamp)

        arm = None
        locked_until = None

        for row in rows:
            now = timestamp(row)

            if locked_until is not None and now < locked_until:
                continue

            if arm is None:
                arm = row
                continue

            gap = (
                now - timestamp(arm)
            ).total_seconds() / 60

            if gap < min_minutes:
                continue

            if gap > max_minutes:
                arm = row
                continue

            fields = (
                "spy_from_open",
                "qqq_from_open",
                "iwm_from_open",
            )

            if any(
                arm.get(x) is None or row.get(x) is None
                for x in fields
            ):
                continue

            all3_worse = all(
                row[x] < arm[x]
                for x in fields
            )

            if not all3_worse:
                continue

            signals.append({
                "decision_date": day,

                "armed_at_utc":
                    arm["captured_at_utc"],

                "confirmed_at_utc":
                    row["captured_at_utc"],

                "confirmation_gap_minutes":
                    gap,

                "arm": arm,
                "entry": row,

                "evaluation": {
                    "path":
                        row["put_15m_tp10_sl10"],

                    "put_ret_15m":
                        row["put_ret_15m"]
                }
            })

            locked_until = (
                now
                + timedelta(minutes=lock_minutes)
            )

            arm = None

    return signals


def main():
    base_cfg = dict(DEFAULTS)

    with BASE_CFG.open(encoding="utf-8") as f:
        base_cfg.update(json.load(f))

    with V02_CFG.open(encoding="utf-8") as f:
        v02 = json.load(f)

    rows = load_rows()

    h06 = reconstruct_h06(rows, base_cfg)

    all_signals = evaluate_state_machine(
        h06,
        v02
    )

    cutoff = v02["prospective_start_after"]

    discovery = [
        s for s in all_signals
        if s["decision_date"] <= cutoff
    ]

    prospective = [
        s for s in all_signals
        if s["decision_date"] > cutoff
    ]

    result = {
        "version": v02["version"],
        "mode": v02["mode"],

        "prospective_start_after":
            cutoff,

        "h06_activations_total":
            len(h06),

        "discovery_replay": {
            "signals": len(discovery),
            "rows": discovery
        },

        "prospective": {
            "signals": len(prospective),
            "rows": prospective
        },

        "warning":
            "Discovery replay is diagnostic only. "
            "Only rows after prospective_start_after "
            "count as scientific evidence."
    }

    OUT.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with OUT.open("w", encoding="utf-8") as f:
        json.dump(
            result,
            f,
            indent=2
        )

    print(
        json.dumps(
            {
                "version":
                    result["version"],

                "h06_activations":
                    result["h06_activations_total"],

                "discovery_replay_signals":
                    result["discovery_replay"]["signals"],

                "prospective_signals":
                    result["prospective"]["signals"],

                "output":
                    str(OUT)
            },
            indent=2
        )
    )


if __name__ == "__main__":
    main()
