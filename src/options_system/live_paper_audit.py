#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Any

TOL = 0.02


def fnum(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def close(a: float, b: float, tol: float = TOL) -> bool:
    return math.isclose(a, b, abs_tol=tol, rel_tol=0.0)


def parse_ts(value: str | None) -> datetime:
    if not value:
        return datetime.max
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def money(x: float) -> str:
    return f"${x:,.2f}"


def pct(x: float) -> str:
    return f"{100*x:.2f}%"


def add_check(checks: list[dict[str, Any]], name: str, status: str, detail: str) -> None:
    checks.append({"name": name, "status": status, "detail": detail})


def latest_session_date(state: dict[str, Any]) -> str | None:
    dates = sorted({str(t.get("decision_date")) for t in (state.get("live_ledger") or []) if t.get("decision_date")})
    return dates[-1] if dates else None


@dataclass
class Event:
    ts: datetime
    priority: int
    kind: str
    trade_index: int
    trade: dict[str, Any]


def audit(state: dict[str, Any], date: str) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    ledger_all = list(state.get("live_ledger") or [])
    ledger = [t for t in ledger_all if str(t.get("decision_date")) == date]
    ledger.sort(key=lambda t: (parse_ts(t.get("entry_time") or t.get("signal_time")), str(t.get("signal_id", ""))))

    if not ledger:
        add_check(checks, "session_has_trades", "FAIL", f"No LIVE PAPER trades found for {date}")
        return {"date": date, "checks": checks, "status": "FAIL", "trade_count": 0}

    duplicate_ids = [sid for sid, n in Counter(str(t.get("signal_id")) for t in ledger).items() if n > 1]
    add_check(checks, "unique_signal_ids", "PASS" if not duplicate_ids else "FAIL",
              "All signal_id values are unique" if not duplicate_ids else f"Duplicates: {duplicate_ids}")

    pnl_errors = []
    entry_cash_errors = []
    budget_errors = []
    quantity_errors = []
    for i, t in enumerate(ledger, 1):
        qty = int(t.get("quantity") or 0)
        if qty != 1:
            quantity_errors.append({"trade": i, "signal_id": t.get("signal_id"), "quantity": qty})
        entry_ask = fnum(t.get("entry_ask"))
        exit_bid = fnum(t.get("exit_bid"))
        capital = fnum(t.get("capital_required"), entry_ask * 100 * max(qty, 1))
        fees = fnum(t.get("fees"))
        gross = fnum(t.get("gross_pnl"))
        net = fnum(t.get("net_pnl"))
        expected_gross = (exit_bid - entry_ask) * 100 * qty
        expected_net = expected_gross - fees
        if not (close(gross, expected_gross) and close(net, expected_net)):
            pnl_errors.append({"trade": i, "signal_id": t.get("signal_id"), "expected_gross": expected_gross,
                               "recorded_gross": gross, "expected_net": expected_net, "recorded_net": net})

        cash_before = fnum(t.get("cash_before"))
        cash_after_entry = fnum(t.get("cash_after_entry"))
        if not close(cash_after_entry, cash_before - capital):
            entry_cash_errors.append({"trade": i, "signal_id": t.get("signal_id"),
                                      "expected": cash_before - capital, "recorded": cash_after_entry})

        sel = t.get("selection") or {}
        risk_fraction = fnum(sel.get("risk_fraction"), fnum(state.get("paper_risk_fraction")))
        sel_cash = fnum(sel.get("cash"), cash_before)
        budget = fnum(sel.get("premium_budget"), sel_cash * risk_fraction)
        if not close(budget, sel_cash * risk_fraction) or capital > budget + TOL:
            budget_errors.append({"trade": i, "signal_id": t.get("signal_id"), "cash": sel_cash,
                                  "risk_fraction": risk_fraction, "budget": budget, "capital": capital})

    add_check(checks, "trade_pnl_formula", "PASS" if not pnl_errors else "FAIL",
              f"All {len(ledger)} closed trades reconcile ASK→BID gross P&L and fees" if not pnl_errors else f"{len(pnl_errors)} trade(s) mismatch")
    add_check(checks, "entry_cash_reconciliation", "PASS" if not entry_cash_errors else "FAIL",
              "Every entry satisfies cash_after_entry = cash_before - capital_required" if not entry_cash_errors else f"{len(entry_cash_errors)} mismatch(es)")
    add_check(checks, "per_entry_budget", "PASS" if not budget_errors else "FAIL",
              "Every entry respects selection.cash × paper risk fraction" if not budget_errors else f"{len(budget_errors)} budget violation(s)")
    add_check(checks, "one_contract_per_entry", "PASS" if not quantity_errors else "WARN",
              "All entries use quantity=1" if not quantity_errors else f"{len(quantity_errors)} entry/entries use quantity != 1")

    events: list[Event] = []
    for idx, t in enumerate(ledger):
        events.append(Event(parse_ts(t.get("entry_time") or t.get("signal_time")), 1, "ENTRY", idx, t))
        if t.get("exit_time"):
            events.append(Event(parse_ts(t.get("exit_time")), 0, "EXIT", idx, t))
    events.sort(key=lambda e: (e.ts, e.priority, e.trade_index))

    first_entry = next(e for e in events if e.kind == "ENTRY")
    running_cash = fnum(first_entry.trade.get("cash_before"))
    daily_start_cash = running_cash
    open_trades: dict[int, dict[str, Any]] = {}
    event_errors = []
    overlaps: list[dict[str, Any]] = []
    exposure_points: list[dict[str, Any]] = []
    max_reserved = 0.0
    max_exposure = 0.0
    max_concurrent = 0
    max_same_hypothesis = 0

    for e in events:
        t = e.trade
        capital = fnum(t.get("capital_required"))
        net = fnum(t.get("net_pnl"))
        if e.kind == "ENTRY":
            recorded_before = fnum(t.get("cash_before"))
            if not close(running_cash, recorded_before):
                event_errors.append({"timestamp": e.ts.isoformat(), "kind": "ENTRY", "signal_id": t.get("signal_id"),
                                     "expected_cash_before": running_cash, "recorded_cash_before": recorded_before})
            same = [x for x in open_trades.values() if x.get("hypothesis") == t.get("hypothesis")]
            if same:
                overlaps.append({"timestamp": e.ts.isoformat(), "signal_id": t.get("signal_id"),
                                 "hypothesis": t.get("hypothesis"), "already_open": len(same), "net_pnl": net})
            running_cash -= capital
            recorded_after = fnum(t.get("cash_after_entry"))
            if not close(running_cash, recorded_after):
                event_errors.append({"timestamp": e.ts.isoformat(), "kind": "ENTRY_AFTER", "signal_id": t.get("signal_id"),
                                     "expected": running_cash, "recorded": recorded_after})
            open_trades[e.trade_index] = t
        else:
            if e.trade_index not in open_trades:
                event_errors.append({"timestamp": e.ts.isoformat(), "kind": "EXIT_WITHOUT_OPEN", "signal_id": t.get("signal_id")})
            running_cash += capital + net
            recorded_after = fnum(t.get("cash_after"))
            if not close(running_cash, recorded_after):
                event_errors.append({"timestamp": e.ts.isoformat(), "kind": "EXIT_AFTER", "signal_id": t.get("signal_id"),
                                     "expected": running_cash, "recorded": recorded_after})
            open_trades.pop(e.trade_index, None)

        reserved = sum(fnum(x.get("capital_required")) for x in open_trades.values())
        cost_basis_equity = running_cash + reserved
        exposure = reserved / cost_basis_equity if cost_basis_equity > 0 else 0.0
        by_hyp = Counter(str(x.get("hypothesis")) for x in open_trades.values())
        max_reserved = max(max_reserved, reserved)
        max_exposure = max(max_exposure, exposure)
        max_concurrent = max(max_concurrent, len(open_trades))
        max_same_hypothesis = max(max_same_hypothesis, max(by_hyp.values(), default=0))
        exposure_points.append({"timestamp": e.ts.isoformat(), "after_event": e.kind,
                                "open_positions": len(open_trades), "reserved_capital": round(reserved, 10),
                                "cost_basis_equity": round(cost_basis_equity, 10), "exposure_fraction": exposure})

    add_check(checks, "event_cash_timeline", "PASS" if not event_errors else "FAIL",
              "Entry/exit event timeline reconciles exactly" if not event_errors else f"{len(event_errors)} event cash mismatch(es)")

    closed = [t for t in ledger if t.get("status") == "CLOSED"]
    open_for_date = [t for t in ledger if t.get("status") != "CLOSED"]
    add_check(checks, "all_session_trades_closed", "PASS" if not open_for_date else "FAIL",
              f"All {len(closed)} session trades are CLOSED" if not open_for_date else f"{len(open_for_date)} trade(s) not CLOSED")

    pnl = sum(fnum(t.get("net_pnl")) for t in closed)
    gross_profit = sum(max(fnum(t.get("net_pnl")), 0.0) for t in closed)
    gross_loss = -sum(min(fnum(t.get("net_pnl")), 0.0) for t in closed)
    wins = sum(fnum(t.get("net_pnl")) > 0 for t in closed)
    losses = sum(fnum(t.get("net_pnl")) < 0 for t in closed)
    fees = sum(fnum(t.get("fees")) for t in closed)
    final_event_cash = running_cash
    add_check(checks, "daily_pnl_cash_bridge", "PASS" if close(daily_start_cash + pnl, final_event_cash) else "FAIL",
              f"{money(daily_start_cash)} + {money(pnl)} = {money(final_event_cash)}")

    last_ledger_date = max((str(t.get("decision_date")) for t in ledger_all if t.get("decision_date")), default=date)
    if date == last_ledger_date and not open_trades:
        state_cash = fnum(state.get("cash"))
        add_check(checks, "state_final_cash", "PASS" if close(final_event_cash, state_cash) else "FAIL",
                  f"Event cash {money(final_event_cash)} vs state cash {money(state_cash)}")
        top_pnl = fnum(state.get("realized_net_pnl"))
        epoch_same_day = str(state.get("live_start_utc", "")).startswith(date)
        if epoch_same_day:
            add_check(checks, "state_realized_pnl", "PASS" if close(pnl, top_pnl) else "FAIL",
                      f"Session P&L {money(pnl)} vs state realized P&L {money(top_pnl)}")

    pending = int(state.get("pending_reconciliation_positions") or 0)
    add_check(checks, "pending_reconciliation", "PASS" if pending == 0 else "FAIL", f"pending_reconciliation_positions={pending}")

    risk_fraction = fnum(state.get("paper_risk_fraction"))
    if risk_fraction and max_exposure > risk_fraction + TOL / 100:
        add_check(checks, "aggregate_exposure_vs_entry_fraction", "WARN",
                  f"Max aggregate cost-basis exposure {pct(max_exposure)} exceeds per-entry paper fraction {pct(risk_fraction)}")
    else:
        add_check(checks, "aggregate_exposure_vs_entry_fraction", "PASS",
                  f"Max aggregate cost-basis exposure {pct(max_exposure)}")

    overlap_pnl = sum(fnum(x.get("net_pnl")) for x in overlaps)
    add_check(checks, "same_hypothesis_overlap", "WARN" if overlaps else "PASS",
              f"{len(overlaps)} entry/entries opened while the same hypothesis was already open; their net P&L={money(overlap_pnl)}" if overlaps else "No same-hypothesis overlap")

    by_hypothesis: dict[str, dict[str, Any]] = {}
    for h, rows in defaultdict(list, {h: [t for t in closed if t.get("hypothesis") == h] for h in {t.get("hypothesis") for t in closed}}).items():
        hpnl = sum(fnum(t.get("net_pnl")) for t in rows)
        hwins = sum(fnum(t.get("net_pnl")) > 0 for t in rows)
        by_hypothesis[str(h)] = {"trades": len(rows), "wins": hwins, "losses": len(rows)-hwins,
                                 "win_rate": hwins/len(rows) if rows else None, "net_pnl": hpnl}

    by_exit: dict[str, dict[str, Any]] = {}
    for reason in sorted({str(t.get("exit_reason")) for t in closed}):
        rows = [t for t in closed if str(t.get("exit_reason")) == reason]
        by_exit[reason] = {"trades": len(rows), "net_pnl": sum(fnum(t.get("net_pnl")) for t in rows)}

    failures = [c for c in checks if c["status"] == "FAIL"]
    warnings = [c for c in checks if c["status"] == "WARN"]
    status = "FAIL" if failures else ("PASS_WITH_WARNINGS" if warnings else "PASS")

    return {
        "version": "live_paper_audit_v1",
        "date": date,
        "epoch_id": state.get("epoch_id"),
        "status": status,
        "checks": checks,
        "summary": {
            "daily_start_cash": daily_start_cash,
            "daily_end_cash": final_event_cash,
            "net_pnl": pnl,
            "return_fraction": pnl / daily_start_cash if daily_start_cash else None,
            "trades": len(closed), "wins": wins, "losses": losses,
            "win_rate": wins / len(closed) if closed else None,
            "gross_profit": gross_profit, "gross_loss": gross_loss,
            "profit_factor": gross_profit / gross_loss if gross_loss else None,
            "fees": fees,
            "largest_win": max((fnum(t.get("net_pnl")) for t in closed), default=0.0),
            "largest_loss": min((fnum(t.get("net_pnl")) for t in closed), default=0.0),
            "max_reserved_capital": max_reserved,
            "max_cost_basis_exposure_fraction": max_exposure,
            "max_concurrent_positions": max_concurrent,
            "max_same_hypothesis_concurrent": max_same_hypothesis,
            "same_hypothesis_overlap_entries": len(overlaps),
            "same_hypothesis_overlap_pnl": overlap_pnl,
        },
        "by_hypothesis": by_hypothesis,
        "by_exit_reason": by_exit,
        "overlaps": overlaps,
        "exposure_timeline": exposure_points,
        "diagnostics": {
            "pnl_errors": pnl_errors,
            "entry_cash_errors": entry_cash_errors,
            "event_cash_errors": event_errors,
            "budget_errors": budget_errors,
            "quantity_errors": quantity_errors,
            "duplicate_signal_ids": duplicate_ids,
        },
    }


def render_text(r: dict[str, Any]) -> str:
    s = r.get("summary", {})
    lines = [
        "=" * 78,
        f"OPTIONS-SYSTEM LIVE PAPER AUDIT · {r.get('date')}",
        "=" * 78,
        f"STATUS: {r.get('status')}",
        f"EPOCH:  {r.get('epoch_id')}",
        "",
        f"Start cash:        {money(fnum(s.get('daily_start_cash')))}",
        f"End cash:          {money(fnum(s.get('daily_end_cash')))}",
        f"Net P&L:           {money(fnum(s.get('net_pnl')))}",
        f"Return:            {pct(fnum(s.get('return_fraction')))}",
        f"Trades:            {s.get('trades', 0)}  (W {s.get('wins', 0)} / L {s.get('losses', 0)})",
        f"Win rate:          {pct(fnum(s.get('win_rate')))}",
        f"Profit factor:     {s.get('profit_factor') if s.get('profit_factor') is not None else 'n/a'}",
        f"Fees:              {money(fnum(s.get('fees')))}",
        f"Max exposure:      {pct(fnum(s.get('max_cost_basis_exposure_fraction')))}",
        f"Max concurrent:    {s.get('max_concurrent_positions', 0)}",
        f"Max same hyp.:     {s.get('max_same_hypothesis_concurrent', 0)}",
        f"Overlap entries:   {s.get('same_hypothesis_overlap_entries', 0)} ({money(fnum(s.get('same_hypothesis_overlap_pnl')))} P&L)",
        "", "CHECKS"
    ]
    for c in r.get("checks", []):
        lines.append(f"[{c['status']:<4}] {c['name']}: {c['detail']}")
    lines.extend(["", "BY HYPOTHESIS"])
    for h, x in sorted((r.get("by_hypothesis") or {}).items()):
        lines.append(f"- {h}: {x['trades']} trades · {money(fnum(x['net_pnl']))} · win rate {pct(fnum(x['win_rate']))}")
    lines.extend(["", "BY EXIT"])
    for reason, x in sorted((r.get("by_exit_reason") or {}).items()):
        lines.append(f"- {reason}: {x['trades']} trades · {money(fnum(x['net_pnl']))}")
    lines.extend(["", "OVERLAPS"])
    if not r.get("overlaps"):
        lines.append("- none")
    else:
        for x in r["overlaps"]:
            lines.append(f"- {x['timestamp']} · {x['hypothesis']} · already_open={x['already_open']} · trade P&L {money(fnum(x['net_pnl']))}")
    lines.append("")
    return "\n".join(lines)
