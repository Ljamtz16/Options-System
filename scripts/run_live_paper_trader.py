import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from options_system.option_costs import one_contract_trade, daily_regulatory_fees
from options_system.prospective_execution_gate import evaluate_execution
from options_system.intraday_session import position_quote,finalize_positions,snapshot_close
from options_system.executable_contracts import select_signal
from options_system.entry_controls import update_session_risk, entry_block
from options_system.prospective_paper_trader import (
    build_paper_signals,
    option_quote,
)

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / "artifacts" / "intraday"

TRACKER = ROOT / "data/processed/intraday/prospective_hypothesis_tracker_v02.csv"
FROZEN = A / "FROZEN_HYPOTHESES_V02.json"
RISK = A / "PROSPECTIVE_RISK_GATE_V01.json"

REPLAY = A / "PAPER_TRADING_REPLAY_V01.json"
STATE = A / "PAPER_TRADING_LIVE_STATE_V01.json"
CONTROL = A / "PAPER_TRADING_CONTROL_V01.json"

TP = 0.10
SL = -0.10
MAX_CONTRACTS = 1


def dt(x):
    return datetime.fromisoformat(x.replace("Z", "+00:00"))


def load_snapshots():
    out = []
    for p in sorted((ROOT / "data/raw/prospective").glob("spy_options_*.json")):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if d.get("captured_at_utc"):
            out.append(d)

    return sorted(out, key=lambda x: x["captured_at_utc"])


tracker_rows = (
    list(csv.DictReader(TRACKER.open(encoding="utf-8")))
    if TRACKER.exists()
    else []
)

frozen = json.loads(FROZEN.read_text(encoding="utf-8"))
risk_gate = json.loads(RISK.read_text(encoding="utf-8"))

if CONTROL.exists():
    control = json.loads(CONTROL.read_text(encoding="utf-8"))
else:
    control = {
        "version": "v0.1",
        "risk_fraction": 0.20,
        "allowed_fractions": [0.0, 0.2, 0.4, 0.6, 0.8],
        "scope": "PAPER_TRADING_ONLY",
        "scientific_risk_gate_unchanged": True,
    }

paper_fraction = float(control.get("risk_fraction", 0.20))

paper_gate = dict(risk_gate)
paper_gate["allowed_max_fraction"] = paper_fraction
paper_gate["status"] = "ACTIVE" if paper_fraction > 0 else "BLOCKED"

snapshots = load_snapshots()

signals = build_paper_signals(
    tracker_rows,
    frozen["hypotheses"],
    frozen["frozen_at"],
)

signals_by_time = {}
for x in signals:
    signals_by_time.setdefault(x["signal_time"], []).append(x)


# ------------------------------------------------------------
# Bootstrap LIVE state from validated causal replay
# ------------------------------------------------------------

if not STATE.exists():
    if not REPLAY.exists():
        raise SystemExit("REPLAY_REQUIRED: run replay_prospective_paper_trader.py first")

    replay = json.loads(REPLAY.read_text(encoding="utf-8"))

    latest_snapshot = (
        snapshots[-1]["captured_at_utc"]
        if snapshots
        else datetime.now(timezone.utc).isoformat()
    )

    state = {
        "version": "v0.1",
        "mode": "LIVE_PAPER",
        "scientific_evidence": False,
        "purpose": "prospective_execution_simulation_only",

        "live_start_utc": latest_snapshot,

        "initial_cash": replay["initial_cash"],
        "cash": replay["cash"],
        "realized_net_pnl": replay["realized_net_pnl"],

        "seen_signal_ids": [x["signal_id"] for x in signals],

        "open_positions": [],
        "live_ledger": [],

        "causal_replay_summary": {
            "signals_seen": replay["signals_seen"],
            "closed_trades": replay["closed_trades"],
            "blocked_signals": replay["blocked_signals"],
            "net_account_pnl": replay["net_account_pnl"],
            "ending_equity": replay["equity"],
        },

        "last_processed_snapshot_utc": latest_snapshot,
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
    }

    STATE.write_text(json.dumps(state, indent=2), encoding="utf-8")

    print(
        "LIVE_PAPER_BOOTSTRAP",
        "start", latest_snapshot,
        "cash", round(state["cash"], 2),
        "replay_net", round(replay["net_account_pnl"], 2),
    )

    raise SystemExit(0)


state = json.loads(STATE.read_text(encoding="utf-8"))

cash = float(state["cash"])
realized = float(state.get("realized_net_pnl", 0.0))

seen = set(state.get("seen_signal_ids", []))

open_positions = {
    x["signal_id"]: x
    for x in state.get("open_positions", [])
}

ledger = list(state.get("live_ledger", []))
session_risk = dict(state.get('session_risk') or {})
entry_policy = dict(control.get('entry_controls') or {})

last_processed = state.get("last_processed_snapshot_utc")


# ------------------------------------------------------------
# Process snapshots chronologically
# ------------------------------------------------------------

for snapshot in snapshots:
    now_s = snapshot["captured_at_utc"]

    if last_processed and dt(now_s) <= dt(last_processed):
        continue

    now = dt(now_s)
    if now > datetime.now(timezone.utc):
        continue

    # --------------------------------------------------------
    # 1. Mark existing positions first
    # --------------------------------------------------------

    for sid in list(open_positions):
        pos = open_positions[sid]

        if now <= dt(pos["entry_time"]):
            continue

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
        pos["mfe"] = max(float(pos["mfe"]), ret)
        pos["mae"] = min(float(pos["mae"]), ret)
        pos["marks"] = int(pos["marks"]) + 1

        elapsed = (
            now - dt(pos["entry_time"])
        ).total_seconds() / 60.0

        reason = None

        if ret >= TP:
            reason = "TP10"
        elif ret <= SL:
            reason = "SL10"
        elif elapsed >= float(pos["horizon_min"]):
            reason = "HORIZON"

        if reason is None:
            continue

        qty = int(pos["quantity"])

        model_trade = one_contract_trade(
            pos["entry_ask"],
            ret,
        )

        fee_one = (
            float(daily_regulatory_fees([model_trade])["total"])
            if model_trade
            else 0.0
        )

        fees = fee_one * qty
        gross = (bid - entry) * 100.0 * qty
        net = gross - fees

        # Return sale proceeds to cash.
        cash += bid * 100.0 * qty - fees
        realized += net

        pos.update({
            "status": "CLOSED",
            "exit_time": now_s,
            "exit_bid": bid,
            "exit_reason": reason,
            "gross_pnl": gross,
            "fees": fees,
            "net_pnl": net,
            "cash_after": cash,
        })

        ledger.append(dict(pos))
        del open_positions[sid]

    cash,close_net=finalize_positions(open_positions,ledger,cash,now)
    realized+=close_net
    update_session_risk(session_risk,now,cash,open_positions,ledger)

    # --------------------------------------------------------
    # 2. Handle signals that occur on this snapshot
    # --------------------------------------------------------

    for signal in signals_by_time.get(now_s, []):
        sid = signal["signal_id"]

        if sid in seen:
            continue

        seen.add(sid)
        update_session_risk(session_risk,now,cash,open_positions,ledger)
        block = entry_block(signal,now,open_positions,ledger,session_risk,entry_policy)
        if block:
            ledger.append(dict(signal,mode='LIVE_PAPER',account_kind='LOCAL_SIMULATION',
                               status='BLOCKED',exit_reason=block,net_pnl=None,cash_after=cash))
            continue
        signal = select_signal(snapshot,signal,cash,paper_fraction)

        episode = {
            "contract": signal["contract"],
            "entry_ask": signal["entry_ask"],
            "entry_bid": signal["entry_bid"],
            "entry_ask_size": signal["entry_ask_size"],
            "entry_bid_size": signal["entry_bid_size"],
        }

        gate = evaluate_execution(
            episode,
            paper_gate,
            cash=cash,
        )

        record = {
            **signal,
            "mode": "LIVE_PAPER",
            "account_kind": "LOCAL_SIMULATION",
            "execution_gate": gate,
            "cash_before": cash,
        }

        if gate["status"] != "PASS":
            ledger.append({
                **record,
                "status": "BLOCKED",
                "exit_reason": "EXECUTION_GATE",
                "gross_pnl": 0.0,
                "fees": 0.0,
                "net_pnl": 0.0,
                "cash_after": cash,
            })
            continue

        max_qty = int(
            gate.get("max_contracts_by_risk_budget") or 0
        )

        qty = min(MAX_CONTRACTS,max_qty)

        if qty < 1:
            ledger.append({
                **record,
                "status": "BLOCKED",
                "exit_reason": "NO_ALLOWED_QUANTITY",
                "gross_pnl": 0.0,
                "fees": 0.0,
                "net_pnl": 0.0,
                "cash_after": cash,
            })
            continue

        ask = float(signal["entry_ask"])
        capital = ask * 100.0 * qty

        if capital > cash:
            ledger.append({
                **record,
                "status": "BLOCKED",
                "exit_reason": "INSUFFICIENT_CASH",
                "gross_pnl": 0.0,
                "fees": 0.0,
                "net_pnl": 0.0,
                "cash_after": cash,
            })
            continue

        cash -= capital

        open_positions[sid] = {
            **record,

            "status": "OPEN",
            "session_close_at_utc":snapshot_close(snapshot),
            "last_quote_time":None,
            "quantity": qty,
            "capital_required": capital,

            "entry_time": now_s,
            "entry_quote_time":signal.get('entry_quote_time'),

            "last_bid": signal.get("entry_bid"),
            "last_mark_time": now_s,
            "unrealized_return": None,

            "mfe": 0.0,
            "mae": 0.0,
            "marks": 0,

            "cash_after_entry": cash,
        }

    last_processed = now_s


cash,close_net=finalize_positions(open_positions,ledger,cash,datetime.now(timezone.utc))
realized+=close_net

# ------------------------------------------------------------
# Equity
# ------------------------------------------------------------

reserved = sum(
    float(x["capital_required"])
    for x in open_positions.values()
)

unrealized = 0.0

for x in open_positions.values():
    bid = x.get("last_bid")

    if bid not in (None, ""):
        unrealized += (
            float(bid) - float(x["entry_ask"])
        ) * 100.0 * int(x["quantity"])

equity = cash + reserved + unrealized


state.update({
    "mode":"LIVE_PAPER",
    "account_kind":"LOCAL_SIMULATION",
    "entry_controls":entry_policy,
    "session_risk":session_risk,
    "contract_selection_version":"executable_contract_v1",
    "simulation_version":"intraday_session_v2",
    "pending_reconciliation_positions":sum(bool(x.get("pending_reconciliation")) for x in open_positions.values()),
    "equity_is_estimate":any(x.get("pending_reconciliation") for x in open_positions.values()),
    "paper_risk_fraction": paper_fraction,
    "scientific_risk_fraction": float(risk_gate.get("allowed_max_fraction") or 0),
    "cash": cash,
    "reserved_capital": reserved,
    "unrealized_pnl": unrealized,
    "realized_net_pnl": realized,
    "equity": equity,

    "net_account_pnl": equity - float(state["initial_cash"]),

    "seen_signal_ids": sorted(seen),

    "open_positions": sorted(
        open_positions.values(),
        key=lambda x: x["entry_time"],
    ),

    "live_ledger": ledger,

    "closed_live_trades": sum(
        x.get("status") == "CLOSED"
        for x in ledger
    ),

    "blocked_live_signals": sum(
        x.get("status") == "BLOCKED"
        for x in ledger
    ),

    "last_processed_snapshot_utc": last_processed,
    "updated_at_utc": datetime.now(timezone.utc).isoformat(),
})

STATE.write_text(
    json.dumps(state, indent=2),
    encoding="utf-8",
)

print(
    "LIVE_PAPER_OK",
    "cash", round(state["cash"], 2),
    "equity", round(state["equity"], 2),
    "open", len(state["open_positions"]),
    "closed", state["closed_live_trades"],
    "blocked", state["blocked_live_signals"],
    "net", round(state["net_account_pnl"], 2),
)
