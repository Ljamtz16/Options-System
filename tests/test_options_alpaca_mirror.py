from copy import deepcopy

import pytest

from options_system.options_alpaca_mirror import MirrorConfig, run_mirror


class FakeClient:
    def __init__(self):
        self.orders = {}
        self.submissions = []

    def submit_option_market(self, symbol, qty, side, position_intent, client_order_id):
        price = "2.05" if side == "buy" else "2.45"
        order = {
            "id": f"id-{client_order_id}",
            "client_order_id": client_order_id,
            "status": "filled",
            "symbol": symbol,
            "qty": str(qty),
            "filled_qty": str(qty),
            "filled_avg_price": price,
            "filled_at": "2026-10-09T13:31:00Z",
        }
        self.orders[client_order_id] = order
        self.submissions.append((side, symbol, qty, position_intent, client_order_id))
        return deepcopy(order)

    def order_by_client_id(self, client_order_id):
        if client_order_id not in self.orders:
            raise RuntimeError("order not found")
        return deepcopy(self.orders[client_order_id])

    def cancel_order(self, order_id):
        for order in self.orders.values():
            if order.get("id") == order_id:
                order["status"] = "canceled"
                return {}
        raise RuntimeError("order not found")


def cfg(submit=False):
    return MirrorConfig(
        enabled=True,
        submit_orders=submit,
        key_id="paper-key",
        secret_key="paper-secret",
        mirror_start_utc="2026-10-09T13:30:00Z",
        shadow_capital=1000.0,
    )


def open_trade():
    return {
        "signal_id": "H01:2026-10-09T13:30:05Z",
        "hypothesis": "CALL_FLOW_REVERSAL_V01",
        "contract": "SPY261012C00775000",
        "quantity": 1,
        "status": "OPEN",
        "entry_time": "2026-10-09T13:30:05Z",
        "entry_ask": 2.00,
        "entry_bid": 1.98,
    }


def test_dry_run_plans_open_trade_without_persisting_fake_order():
    state = {"open_positions": [open_trade()], "live_ledger": []}
    mirror, actions = run_mirror(state, {"trades": {}}, cfg(submit=False), client=FakeClient())
    assert actions[0]["action"] == "BUY_TO_OPEN"
    assert mirror["trades"] == {}
    assert mirror["paper_only"] is True


def test_closed_trade_never_backfills_a_missed_entry():
    t = open_trade()
    t.update(status="CLOSED", exit_time="2026-10-09T13:40:00Z", exit_bid=2.20, net_pnl=19.89)
    mirror, actions = run_mirror({"open_positions": [], "live_ledger": [t]}, {"trades": {}}, cfg(), client=FakeClient())
    row = mirror["trades"][t["signal_id"]]
    assert row["status"] == "SKIPPED_MISSED_LIVE_ENTRY"
    assert actions == [{"action": "SKIP_MISSED_ENTRY", "signal_id": t["signal_id"]}]


def test_live_open_then_close_is_idempotently_mirrored():
    client = FakeClient()
    t = open_trade()
    local_open = {"open_positions": [t], "live_ledger": []}
    mirror, actions = run_mirror(local_open, {"trades": {}}, cfg(submit=True), client=client)
    assert actions[0]["action"] == "BUY_TO_OPEN"
    assert mirror["trades"][t["signal_id"]]["status"] == "OPEN_FILLED"
    assert len(client.submissions) == 1

    closed = deepcopy(t)
    closed.update(
        status="CLOSED",
        exit_time="2026-10-09T13:40:00Z",
        exit_bid=2.40,
        gross_pnl=40.0,
        net_pnl=39.89,
        exit_reason="TP10",
    )
    local_closed = {"open_positions": [], "live_ledger": [closed]}
    mirror, actions = run_mirror(local_closed, mirror, cfg(submit=True), client=client)
    row = mirror["trades"][t["signal_id"]]
    assert actions[0]["action"] == "SELL_TO_CLOSE"
    assert row["status"] == "CLOSED_FILLED"
    assert row["broker_gross_pnl"] == pytest.approx(40.0)
    assert row["entry_slippage_vs_local_ask"] == pytest.approx(0.05)
    assert row["exit_slippage_vs_local_bid"] == pytest.approx(0.05)
    assert row["gross_pnl_delta_vs_local"] == pytest.approx(0.0)
    assert len(client.submissions) == 2

    mirror2, actions2 = run_mirror(local_closed, mirror, cfg(submit=True), client=client)
    assert actions2 == []
    assert len(client.submissions) == 2
    assert mirror2["trades"][t["signal_id"]]["status"] == "CLOSED_FILLED"


def test_existing_broker_entry_is_recovered_after_local_state_restart():
    client = FakeClient()
    t = open_trade()
    cid = "optsys_entry_" + __import__("hashlib").sha1(t["signal_id"].encode("utf-8")).hexdigest()[:24]
    client.orders[cid] = {
        "id": f"id-{cid}",
        "client_order_id": cid,
        "status": "filled",
        "symbol": t["contract"],
        "qty": "1",
        "filled_qty": "1",
        "filled_avg_price": "2.05",
        "filled_at": "2026-10-09T13:31:00Z",
    }
    mirror, actions = run_mirror(
        {"open_positions": [t], "live_ledger": []},
        {"trades": {}},
        cfg(submit=True),
        client=client,
    )
    assert actions[0]["action"] == "BUY_TO_OPEN"
    assert mirror["trades"][t["signal_id"]]["status"] == "OPEN_FILLED"
    assert client.submissions == []


def test_pending_entry_is_canceled_if_local_trade_closes_first():
    class PendingClient(FakeClient):
        def submit_option_market(self, symbol, qty, side, position_intent, client_order_id):
            if side == "sell":
                return super().submit_option_market(symbol, qty, side, position_intent, client_order_id)
            order = {
                "id": f"id-{client_order_id}",
                "client_order_id": client_order_id,
                "status": "accepted",
                "symbol": symbol,
                "qty": str(qty),
                "filled_qty": "0",
                "filled_avg_price": None,
            }
            self.orders[client_order_id] = order
            self.submissions.append((side, symbol, qty, position_intent, client_order_id))
            return deepcopy(order)

    client = PendingClient()
    t = open_trade()
    mirror, _ = run_mirror({"open_positions": [t], "live_ledger": []}, {"trades": {}}, cfg(submit=True), client=client)
    assert mirror["trades"][t["signal_id"]]["status"] == "ENTRY_SUBMITTED"

    closed = deepcopy(t)
    closed.update(status="CLOSED", exit_time="2026-10-09T13:40:00Z", exit_bid=1.90, gross_pnl=-10.0, net_pnl=-10.11, exit_reason="SL10")
    mirror, actions = run_mirror({"open_positions": [], "live_ledger": [closed]}, mirror, cfg(submit=True), client=client)
    assert any(a["action"] == "CANCEL_ENTRY" for a in actions)
    assert mirror["trades"][t["signal_id"]]["status"] == "LOCAL_CLOSED_WITHOUT_BROKER_ENTRY_FILL"
    assert len(client.submissions) == 1


def open_clock(minutes=60):
    return {"is_open": True, "timestamp": "2026-10-09T15:00:00-04:00", "next_close": "2026-10-09T16:00:00-04:00"} if minutes == 60 else {"is_open": True, "timestamp": "2026-10-09T15:58:00-04:00", "next_close": "2026-10-09T16:00:00-04:00"}


def test_expired_exit_retries_when_broker_position_still_exists():
    client = FakeClient(); t = open_trade()
    mirror, _ = run_mirror({"open_positions": [t], "live_ledger": []}, {"trades": {}}, cfg(submit=True), client=client)
    closed = deepcopy(t); closed.update(status="CLOSED", exit_time="2026-10-09T13:40:00Z", exit_bid=2.40, gross_pnl=40.0, net_pnl=39.89, exit_reason="TP10")
    sid=t["signal_id"]; row=mirror["trades"][sid]
    expired={"id":"old-exit","client_order_id":"old-exit-cid","status":"expired","symbol":t["contract"],"qty":"1","filled_qty":"0","filled_avg_price":None}
    row["exit_order"]=expired
    client.orders["old-exit-cid"]=deepcopy(expired)
    positions=[{"symbol":t["contract"],"qty":"1"}]
    mirror, actions = run_mirror({"open_positions": [], "live_ledger": [closed]}, mirror, cfg(submit=True), client=client, broker_positions=positions, broker_clock=open_clock())
    assert any(a["action"] == "RETRY_SELL_TO_CLOSE" for a in actions)
    assert mirror["trades"][sid]["status"] == "CLOSED_FILLED"
    assert mirror["trades"][sid]["exit_retry_count"] == 1
    assert len(mirror["trades"][sid]["exit_history"]) == 1


def test_expired_exit_waits_for_market_open():
    client = FakeClient(); t=open_trade()
    cid="optsys_entry_"+__import__("hashlib").sha1(t["signal_id"].encode()).hexdigest()[:24]
    entry={"id":"entry","client_order_id":cid,"status":"filled","symbol":t["contract"],"qty":"1","filled_qty":"1","filled_avg_price":"2.05"}
    expired={"id":"exit","client_order_id":"exit-old","status":"expired","symbol":t["contract"],"qty":"1","filled_qty":"0","filled_avg_price":None}
    client.orders[cid]=deepcopy(entry);client.orders["exit-old"]=deepcopy(expired)
    row={"signal_id":t["signal_id"],"contract":t["contract"],"quantity":1,"local_entry_time":t["entry_time"],"local_entry_ask":2.0,"entry_order":entry,"exit_order":expired,"status":"EXIT_EXPIRED"}
    closed=deepcopy(t);closed.update(status="CLOSED",exit_time="2026-10-09T19:59:00Z",exit_bid=2.0,gross_pnl=0,net_pnl=-.11,exit_reason="SESSION_CLOSE")
    clock={"is_open":False,"timestamp":"2026-10-09T17:00:00-04:00","next_close":"2026-10-12T16:00:00-04:00"}
    mirror, actions=run_mirror({"open_positions":[],"live_ledger":[closed]},{"trades":{t["signal_id"]:row}},cfg(submit=True),client=client,broker_positions=[{"symbol":t["contract"],"qty":"1"}],broker_clock=clock)
    assert actions == []
    assert mirror["trades"][t["signal_id"]]["status"] == "EXIT_WAITING_MARKET_OPEN"


def test_broker_eod_safety_closes_before_local_session_close():
    client=FakeClient();t=open_trade()
    mirror,_=run_mirror({"open_positions":[t],"live_ledger":[]},{"trades":{}},cfg(submit=True),client=client)
    mirror,actions=run_mirror({"open_positions":[t],"live_ledger":[]},mirror,cfg(submit=True),client=client,broker_positions=[{"symbol":t["contract"],"qty":"1"}],broker_clock=open_clock(minutes=2))
    assert any(a["reason"] == "BROKER_EOD_SAFETY" for a in actions if a["action"] == "SELL_TO_CLOSE")
    assert mirror["trades"][t["signal_id"]]["status"] == "BROKER_CLOSED_EOD_LOCAL_OPEN"


def test_residual_broker_position_blocks_new_entry():
    t=open_trade();client=FakeClient()
    mirror,actions=run_mirror({"open_positions":[t],"live_ledger":[]},{"trades":{}},cfg(submit=True),client=client,broker_positions=[{"symbol":"SPY261019C00780000","qty":"1"}],broker_clock=open_clock())
    assert mirror["trades"] == {}
    assert actions[0]["action"] == "BLOCK_ENTRY_BROKER_RECONCILIATION"
    assert client.submissions == []
