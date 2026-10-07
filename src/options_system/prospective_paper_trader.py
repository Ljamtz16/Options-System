from __future__ import annotations

from datetime import datetime
from typing import Any

from options_system.option_costs import one_contract_trade, daily_regulatory_fees
from options_system.prospective_execution_gate import evaluate_execution
from options_system.intraday_session import position_quote,finalize_positions,snapshot_close
from options_system.executable_contracts import select_signal
from options_system.entry_controls import update_session_risk, entry_block


DEFAULT_PAPER_POLICY = {
    "initial_cash": 1000.0,
    "tp": 0.10,
    "sl": -0.10,
    "default_gap_minutes": 6,
    "max_contracts_per_trade": 1,
    "select_executable_contract": True,
    "entry_controls": {},
}


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def option_quote(snapshot: dict[str, Any], contract: str) -> dict[str, Any] | None:
    """
    Return the exact option quote for an OCC contract.

    Raw layout:
      payload.options.snapshot.snapshots.<OCC_SYMBOL>.latestQuote
    """
    try:
        contract_data = (
            snapshot["payload"]["options"]["snapshot"]["snapshots"][contract]
        )
    except (KeyError, TypeError):
        return None

    q = contract_data.get("latestQuote") or {}

    if not q:
        return None

    return {
        "bid": q.get("bp"),
        "ask": q.get("ap"),
        "bid_size": q.get("bs"),
        "ask_size": q.get("as"),
        "quote_time": q.get("t"),
    }


def build_paper_signals(
    tracker_rows: list[dict[str, Any]],
    hypotheses: list[dict[str, Any]],
    frozen_at: str,
    default_gap_minutes: float = 6,
) -> list[dict[str, Any]]:
    """
    Convert frozen-hypothesis activations into deterministic paper episodes.

    This DOES NOT change hypothesis definitions.
    H01/H02 receive only a paper-trading grouping policy.
    """
    signals: list[dict[str, Any]] = []

    for hypothesis in hypotheses:
        hid = hypothesis["id"]
        side = hypothesis["side"]
        horizon = int(hypothesis["horizon_min"])

        episode_policy = hypothesis.get("episode_policy") or {}
        gap = float(episode_policy.get("gap_minutes", default_gap_minutes))

        active = []

        for row in tracker_rows:
            decision_date = row.get("decision_date", "")

            if decision_date <= frozen_at:
                continue

            active_ids = [
                x
                for x in (row.get("active_hypotheses") or "").split(";")
                if x
            ]

            if hid in active_ids:
                active.append(row)

        active.sort(key=lambda x: x.get("captured_at_utc", ""))

        groups = []
        current = None
        previous_ts = None

        for row in active:
            ts = _dt(row["captured_at_utc"])

            new_episode = (
                current is None
                or previous_ts is None
                or row.get("decision_date") != current["decision_date"]
                or (ts - previous_ts).total_seconds() > gap * 60
            )

            if new_episode:
                current = {
                    "decision_date": row.get("decision_date"),
                    "rows": [row],
                }
                groups.append(current)
            else:
                current["rows"].append(row)

            previous_ts = ts

        for i, group in enumerate(groups, 1):
            entry = group["rows"][0]

            signals.append(
                {
                    "signal_id": f"{hid}:{group['decision_date']}:P{i}",
                    "hypothesis": hid,
                    "decision_date": group["decision_date"],
                    "signal_time": entry["captured_at_utc"],
                    "activation_count": len(group["rows"]),
                    "side": side,
                    "horizon_min": horizon,
                    "contract": entry.get(f"{side}_contract"),
                    "entry_ask": entry.get(f"{side}_entry_ask"),
                    "entry_bid": entry.get(f"{side}_entry_bid"),
                    "entry_ask_size": entry.get(f"{side}_entry_ask_size"),
                    "entry_bid_size": entry.get(f"{side}_entry_bid_size"),
                }
            )

    return sorted(signals, key=lambda x: x["signal_time"])


def replay_paper_account(
    snapshots: list[dict[str, Any]],
    signals: list[dict[str, Any]],
    risk_gate: dict[str, Any],
    policy: dict[str, Any] | None = None,
    as_of: datetime | None = None,
) -> dict[str, Any]:
    policy = {**DEFAULT_PAPER_POLICY, **(policy or {})}

    initial_cash = float(policy["initial_cash"])
    cash = initial_cash

    signal_by_time: dict[str, list[dict[str, Any]]] = {}

    for signal in signals:
        signal_by_time.setdefault(signal["signal_time"], []).append(signal)

    snapshots = sorted(
        snapshots,
        key=lambda x: x.get("captured_at_utc", ""),
    )

    open_positions: dict[str, dict[str, Any]] = {}
    ledger: list[dict[str, Any]] = []
    session_risk = {}
    equity_curve = []

    for snapshot in snapshots:
        now_s = snapshot.get("captured_at_utc")
        if not now_s:
            continue

        now = _dt(now_s)
        if as_of is not None and now > as_of:
            continue

        # ----------------------------------------------------------
        # 1. Mark / close positions that were already open
        # ----------------------------------------------------------
        for signal_id in list(open_positions):
            pos = open_positions[signal_id]

            q = position_quote(snapshot,pos,option_quote(snapshot, pos["contract"]))

            if not q or q.get("bid") in (None, ""):
                continue

            bid = float(q["bid"])
            entry = float(pos["entry_ask"])

            ret = (bid - entry) / entry

            pos["last_bid"] = bid
            pos["last_mark_time"] = now_s
            pos["last_quote_time"] = q["quote_time"]
            pos["unrealized_return"] = ret
            pos["mfe"] = max(pos["mfe"], ret)
            pos["mae"] = min(pos["mae"], ret)
            pos["marks"] += 1

            elapsed_min = (
                now - _dt(pos["signal_time"])
            ).total_seconds() / 60.0

            reason = None

            if ret >= float(policy["tp"]):
                reason = "TP10"
            elif ret <= float(policy["sl"]):
                reason = "SL10"
            elif elapsed_min >= float(pos["horizon_min"]):
                reason = "HORIZON"

            if reason is None:
                continue

            exit_return = ret

            model_trade = one_contract_trade(
                pos["entry_ask"],
                exit_return,
            )

            fee = (
                float(daily_regulatory_fees([model_trade])["total"])
                if model_trade
                else 0.0
            )

            qty = int(pos["quantity"])
            exit_value = bid * 100.0 * qty
            gross_pnl = (bid - entry) * 100.0 * qty
            total_fee = fee * qty
            net_pnl = gross_pnl - total_fee

            # Entry capital was removed when opening.
            cash += exit_value - total_fee

            pos.update(
                {
                    "status": "CLOSED",
                    "exit_time": now_s,
                    "exit_bid": bid,
                    "exit_reason": reason,
                    "gross_pnl": gross_pnl,
                    "fees": total_fee,
                    "net_pnl": net_pnl,
                    "cash_after": cash,
                }
            )

            ledger.append(dict(pos))
            del open_positions[signal_id]

        cash,_=finalize_positions(open_positions,ledger,cash,now)
        update_session_risk(session_risk,now,cash,open_positions,ledger)
        equity_curve.append(dict(timestamp=now_s,**session_risk))

        # ----------------------------------------------------------
        # 2. Open signals occurring at this snapshot
        # ----------------------------------------------------------
        for signal in signal_by_time.get(now_s, []):
            update_session_risk(session_risk,now,cash,open_positions,ledger)
            block = entry_block(signal,now,open_positions,ledger,session_risk,policy['entry_controls'])
            if block:
                ledger.append(dict(signal, mode='CAUSAL_REPLAY', account_kind='LOCAL_SIMULATION',
                                   status='BLOCKED', exit_reason=block, net_pnl=None, cash_after=cash))
                continue
            if policy['select_executable_contract']:
                signal = select_signal(snapshot,signal,cash,float(risk_gate.get('allowed_max_fraction') or 0),
                                       policy.get('contract_selection_policy'))
            episode = {
                "contract": signal["contract"],
                "entry_ask": signal["entry_ask"],
                "entry_bid": signal["entry_bid"],
                "entry_ask_size": signal["entry_ask_size"],
                "entry_bid_size": signal["entry_bid_size"],
            }

            execution = evaluate_execution(
                episode,
                risk_gate,
                cash=cash,
            )

            base = {
                **signal,
                "mode": "CAUSAL_REPLAY",
                "account_kind": "LOCAL_SIMULATION",
                "execution_gate": execution,
                "cash_before": cash,
            }

            if execution["status"] != "PASS":
                ledger.append(
                    {
                        **base,
                        "status": "BLOCKED",
                        "exit_reason": "EXECUTION_GATE",
                        "gross_pnl": 0.0,
                        "fees": 0.0,
                        "net_pnl": 0.0,
                        "cash_after": cash,
                    }
                )
                continue

            ask = float(signal["entry_ask"])

            max_by_gate = int(
                execution.get("max_contracts_by_risk_budget") or 0
            )

            qty = min(
                int(policy["max_contracts_per_trade"]),
                max_by_gate,
            )

            if qty < 1:
                ledger.append(
                    {
                        **base,
                        "status": "BLOCKED",
                        "exit_reason": "NO_ALLOWED_QUANTITY",
                        "gross_pnl": 0.0,
                        "fees": 0.0,
                        "net_pnl": 0.0,
                        "cash_after": cash,
                    }
                )
                continue

            capital = ask * 100.0 * qty

            if capital > cash:
                ledger.append(
                    {
                        **base,
                        "status": "BLOCKED",
                        "exit_reason": "INSUFFICIENT_CASH",
                        "gross_pnl": 0.0,
                        "fees": 0.0,
                        "net_pnl": 0.0,
                        "cash_after": cash,
                    }
                )
                continue

            cash -= capital

            open_positions[signal["signal_id"]] = {
                **base,
                "status": "OPEN",
                "session_close_at_utc":snapshot_close(snapshot),
                "last_quote_time":None,
                "quantity": qty,
                "capital_required": capital,
                "entry_time": now_s,
                "entry_quote_time":signal.get('entry_quote_time'),
                "mfe": 0.0,
                "mae": 0.0,
                "marks": 0,
                "last_bid": signal.get("entry_bid"),
                "last_mark_time": now_s,
                "unrealized_return": None,
                "cash_after_entry": cash,
            }

    if snapshots:
        cash,_=finalize_positions(open_positions,ledger,cash,as_of or _dt(snapshots[-1]['captured_at_utc']))
        update_session_risk(session_risk,as_of or _dt(snapshots[-1]['captured_at_utc']),cash,open_positions,ledger)
        equity_curve.append(dict(timestamp=(as_of or _dt(snapshots[-1]['captured_at_utc'])).isoformat(),**session_risk))

    # Open positions at end of available data.
    open_list = sorted(
        open_positions.values(),
        key=lambda x: x["signal_time"],
    )

    unrealized = 0.0

    for pos in open_list:
        if pos.get("last_bid") not in (None, ""):
            unrealized += (
                float(pos["last_bid"]) - float(pos["entry_ask"])
            ) * 100.0 * int(pos["quantity"])

    realized = sum(
        float(x.get("net_pnl") or 0)
        for x in ledger
        if x.get("status") == "CLOSED"
    )

    blocked = sum(
        x.get("status") == "BLOCKED"
        for x in ledger
    )

    closed = sum(
        x.get("status") == "CLOSED"
        for x in ledger
    )

    reserved = sum(
        float(x.get("capital_required") or 0)
        for x in open_list
    )

    equity = cash + reserved + unrealized

    return {
        "version": "v0.1",
        "simulation_version":"intraday_session_v2",
        "pending_reconciliation_positions":sum(bool(x.get("pending_reconciliation")) for x in open_list),
        "equity_is_estimate":any(x.get("pending_reconciliation") for x in open_list),
        "mode": "CAUSAL_REPLAY",
        "account_kind":"LOCAL_SIMULATION",
        "policy":policy,
        "session_risk":session_risk,
        "equity_curve":equity_curve,
        "scientific_evidence": False,
        "purpose": "execution_realism_paper_simulation_only",
        "initial_cash": initial_cash,
        "cash": cash,
        "reserved_capital": reserved,
        "unrealized_pnl": unrealized,
        "realized_net_pnl": realized,
        "equity": equity,
        "net_account_pnl": equity - initial_cash,
        "closed_trades": closed,
        "blocked_signals": blocked,
        "open_positions_count": len(open_list),
        "ledger": ledger,
        "open_positions": open_list,
    }
