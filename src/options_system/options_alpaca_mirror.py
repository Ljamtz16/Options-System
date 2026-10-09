from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

PAPER_BASE_URL = "https://paper-api.alpaca.markets"
TERMINAL_ORDER_STATES = {"filled", "canceled", "expired", "rejected", "replaced"}
NY = ZoneInfo("America/New_York")
BROKER_EXIT_BUFFER_MINUTES = 3.0


def _truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _dt(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _client_id(signal_id: str, action: str) -> str:
    digest = hashlib.sha1(signal_id.encode("utf-8")).hexdigest()[:24]
    return f"optsys_{action}_{digest}"


def load_env_file(path: str | Path | None = None) -> Path | None:
    raw = path or os.getenv("OPTIONS_ALPACA_ENV_FILE") or "~/.config/options-system/options-alpaca-paper.env"
    p = Path(raw).expanduser()
    if not p.exists():
        return None
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key.startswith("OPTIONS_ALPACA_"):
            os.environ.setdefault(key, value.strip())
    return p


@dataclass(frozen=True)
class MirrorConfig:
    enabled: bool
    submit_orders: bool
    key_id: str
    secret_key: str
    mirror_start_utc: str
    shadow_capital: float = 1000.0

    @classmethod
    def from_env(cls) -> "MirrorConfig":
        return cls(
            enabled=_truthy(os.getenv("OPTIONS_ALPACA_PAPER_ENABLED")),
            submit_orders=_truthy(os.getenv("OPTIONS_ALPACA_SUBMIT_ORDERS")),
            key_id=os.getenv("OPTIONS_ALPACA_API_KEY_ID", "").strip(),
            secret_key=os.getenv("OPTIONS_ALPACA_API_SECRET_KEY", "").strip(),
            mirror_start_utc=os.getenv("OPTIONS_ALPACA_MIRROR_START_UTC", "").strip(),
            shadow_capital=float(os.getenv("OPTIONS_ALPACA_SHADOW_CAPITAL", "1000")),
        )

    def validate(self, require_start: bool = True) -> None:
        if not self.key_id or not self.secret_key:
            raise RuntimeError("OPTIONS_ALPACA credentials are missing")
        if require_start and not self.mirror_start_utc:
            raise RuntimeError("OPTIONS_ALPACA_MIRROR_START_UTC is required before mirroring")
        if self.mirror_start_utc and _dt(self.mirror_start_utc) is None:
            raise RuntimeError("Invalid OPTIONS_ALPACA_MIRROR_START_UTC")


class AlpacaPaperClient:
    def __init__(self, key_id: str, secret_key: str, timeout: int = 15):
        self.key_id = key_id
        self.secret_key = secret_key
        self.timeout = timeout
        self.base_url = PAPER_BASE_URL

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None,
                 params: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        if params:
            url += "?" + urlencode(params)
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        headers = {
            "APCA-API-KEY-ID": self.key_id,
            "APCA-API-SECRET-KEY": self.secret_key,
            "Accept": "application/json",
        }
        if body is not None:
            headers["Content-Type"] = "application/json"
        req = Request(url, data=body, headers=headers, method=method)
        try:
            with urlopen(req, timeout=self.timeout) as r:
                raw = r.read().decode("utf-8")
                data = json.loads(raw) if raw else {}
                if isinstance(data, dict):
                    data["_request_id"] = r.headers.get("X-Request-ID")
                return data
        except HTTPError as e:
            body_text = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Alpaca paper HTTP {e.code}: {body_text}") from e

    def account(self) -> dict[str, Any]:
        return self._request("GET", "/v2/account")

    def positions(self) -> list[dict[str, Any]]:
        return self._request("GET", "/v2/positions")

    def clock(self) -> dict[str, Any]:
        return self._request("GET", "/v2/clock")

    def submit_option_market(self, symbol: str, qty: int, side: str,
                             position_intent: str, client_order_id: str) -> dict[str, Any]:
        payload = {
            "symbol": symbol,
            "qty": str(qty),
            "side": side,
            "type": "market",
            "time_in_force": "day",
            "position_intent": position_intent,
            "client_order_id": client_order_id,
        }
        return self._request("POST", "/v2/orders", payload=payload)

    def order_by_client_id(self, client_order_id: str) -> dict[str, Any]:
        return self._request("GET", "/v2/orders:by_client_order_id",
                             params={"client_order_id": client_order_id})

    def cancel_order(self, order_id: str) -> dict[str, Any]:
        return self._request("DELETE", f"/v2/orders/{order_id}")


def _local_records(local_state: dict[str, Any], start_utc: str) -> list[dict[str, Any]]:
    start = _dt(start_utc)
    if start is None:
        return []
    rows: dict[str, dict[str, Any]] = {}
    for t in local_state.get("live_ledger") or []:
        sid = str(t.get("signal_id") or "")
        if not sid or t.get("status") not in {"OPEN", "CLOSED"}:
            continue
        entry = _dt(t.get("entry_time") or t.get("signal_time"))
        if entry and entry >= start:
            rows[sid] = dict(t)
    for t in local_state.get("open_positions") or []:
        sid = str(t.get("signal_id") or "")
        if not sid:
            continue
        entry = _dt(t.get("entry_time") or t.get("signal_time"))
        if entry and entry >= start:
            rows[sid] = dict(t)
    return sorted(rows.values(), key=lambda x: x.get("entry_time") or x.get("signal_time") or "")


def _order_summary(order: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": order.get("id"),
        "client_order_id": order.get("client_order_id"),
        "status": order.get("status"),
        "symbol": order.get("symbol"),
        "qty": order.get("qty"),
        "filled_qty": order.get("filled_qty"),
        "filled_avg_price": order.get("filled_avg_price"),
        "submitted_at": order.get("submitted_at"),
        "filled_at": order.get("filled_at"),
        "canceled_at": order.get("canceled_at"),
        "failed_at": order.get("failed_at"),
        "request_id": order.get("_request_id"),
    }


def _refresh_order(client: AlpacaPaperClient, saved: dict[str, Any] | None) -> dict[str, Any] | None:
    if not saved or not saved.get("client_order_id"):
        return saved
    try:
        return _order_summary(client.order_by_client_id(saved["client_order_id"]))
    except RuntimeError:
        return saved


def _recover_or_submit(client: AlpacaPaperClient, *, signal_id: str, action: str,
                       symbol: str, qty: int, side: str, position_intent: str) -> dict[str, Any]:
    client_order_id = _client_id(signal_id, action)
    try:
        return client.order_by_client_id(client_order_id)
    except RuntimeError:
        return client.submit_option_market(
            symbol=symbol,
            qty=qty,
            side=side,
            position_intent=position_intent,
            client_order_id=client_order_id,
        )


def _broker_position_symbols(positions: list[dict[str, Any]] | None) -> set[str] | None:
    if positions is None:
        return None
    result = set()
    for pos in positions:
        try:
            qty = float(pos.get("qty") or 0)
        except (TypeError, ValueError):
            qty = 0
        if qty:
            result.add(str(pos.get("symbol") or ""))
    return result


def _clock_window(clock: dict[str, Any] | None) -> tuple[bool, float | None]:
    if clock is None:
        return True, None
    is_open = bool(clock.get("is_open"))
    try:
        now = _dt(clock.get("timestamp"))
        close = _dt(clock.get("next_close"))
        minutes = None if now is None or close is None else (close - now).total_seconds() / 60.0
    except (TypeError, ValueError):
        minutes = None
    return is_open, minutes


def _finish_broker_trade(mirrored: dict[str, Any], local_closed: bool) -> None:
    entry_fill = float((mirrored.get("entry_order") or {}).get("filled_avg_price") or 0)
    exit_fill = float((mirrored.get("exit_order") or {}).get("filled_avg_price") or 0)
    qty = int(mirrored.get("quantity") or 1)
    broker_gross = (exit_fill - entry_fill) * 100.0 * qty
    mirrored["broker_gross_pnl"] = broker_gross
    if mirrored.get("local_entry_ask") is not None:
        mirrored["entry_slippage_vs_local_ask"] = entry_fill - float(mirrored["local_entry_ask"])
    if mirrored.get("local_exit_bid") is not None:
        mirrored["exit_slippage_vs_local_bid"] = exit_fill - float(mirrored["local_exit_bid"])
    if mirrored.get("local_gross_pnl") is not None:
        mirrored["gross_pnl_delta_vs_local"] = broker_gross - float(mirrored["local_gross_pnl"])
    mirrored["status"] = "CLOSED_FILLED" if local_closed else "BROKER_CLOSED_EOD_LOCAL_OPEN"


def run_mirror(local_state: dict[str, Any], mirror_state: dict[str, Any], config: MirrorConfig,
               client: AlpacaPaperClient | None = None, *,
               broker_positions: list[dict[str, Any]] | None = None,
               broker_clock: dict[str, Any] | None = None) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    config.validate(require_start=True)
    client = client or AlpacaPaperClient(config.key_id, config.secret_key)
    records = mirror_state.setdefault("trades", {})
    actions: list[dict[str, Any]] = []
    position_symbols = _broker_position_symbols(broker_positions)
    market_open, minutes_left = _clock_window(broker_clock)

    for local in _local_records(local_state, config.mirror_start_utc):
        sid = str(local["signal_id"])
        local_status = str(local.get("status") or "")
        symbol = str(local.get("contract") or "")
        mirrored = records.get(sid)

        if mirrored is None and local_status == "CLOSED":
            records[sid] = {
                "signal_id": sid,
                "contract": local.get("contract"),
                "local_entry_time": local.get("entry_time"),
                "local_exit_time": local.get("exit_time"),
                "status": "SKIPPED_MISSED_LIVE_ENTRY",
                "reason": "Trade was already closed before mirror observed an OPEN state",
            }
            actions.append({"action": "SKIP_MISSED_ENTRY", "signal_id": sid})
            continue

        if mirrored is None and local_status == "OPEN":
            if position_symbols:
                actions.append({"action": "BLOCK_ENTRY_BROKER_RECONCILIATION", "signal_id": sid,
                                "broker_positions": sorted(position_symbols)})
                continue
            if broker_clock is not None and (not market_open or
                    (minutes_left is not None and minutes_left <= BROKER_EXIT_BUFFER_MINUTES)):
                actions.append({"action": "BLOCK_ENTRY_CLOSING_WINDOW", "signal_id": sid,
                                "minutes_to_close": minutes_left})
                continue
            plan = {
                "action": "BUY_TO_OPEN",
                "signal_id": sid,
                "symbol": local.get("contract"),
                "qty": int(local.get("quantity") or 1),
                "local_reference_ask": float(local.get("entry_ask") or 0),
            }
            actions.append(plan)
            if not config.submit_orders:
                continue
            order = _recover_or_submit(
                client, signal_id=sid, action="entry", symbol=symbol,
                qty=int(local.get("quantity") or 1), side="buy", position_intent="buy_to_open")
            mirrored = {
                "signal_id": sid,
                "hypothesis": local.get("hypothesis"),
                "contract": local.get("contract"),
                "quantity": int(local.get("quantity") or 1),
                "local_entry_time": local.get("entry_time"),
                "local_entry_ask": local.get("entry_ask"),
                "local_exit_time": None,
                "local_exit_bid": None,
                "local_net_pnl": None,
                "entry_order": _order_summary(order),
                "exit_order": None,
                "exit_history": [],
                "exit_retry_count": 0,
                "status": "ENTRY_SUBMITTED",
            }
            records[sid] = mirrored

        if mirrored is None:
            continue

        if config.submit_orders and mirrored.get("entry_order"):
            mirrored["entry_order"] = _refresh_order(client, mirrored.get("entry_order"))
        entry_status = str((mirrored.get("entry_order") or {}).get("status") or "")

        if local_status == "CLOSED":
            mirrored["local_exit_time"] = local.get("exit_time")
            mirrored["local_exit_bid"] = local.get("exit_bid")
            mirrored["local_gross_pnl"] = local.get("gross_pnl")
            mirrored["local_net_pnl"] = local.get("net_pnl")
            mirrored["local_exit_reason"] = local.get("exit_reason")

        if entry_status != "filled":
            if local_status == "CLOSED":
                entry_order = mirrored.get("entry_order") or {}
                if config.submit_orders and entry_order.get("id") and entry_status not in TERMINAL_ORDER_STATES:
                    actions.append({"action": "CANCEL_ENTRY", "signal_id": sid, "order_id": entry_order.get("id")})
                    try:
                        client.cancel_order(str(entry_order["id"]))
                    except RuntimeError as exc:
                        mirrored["entry_cancel_error"] = str(exc)
                    mirrored["entry_order"] = _refresh_order(client, entry_order)
                    entry_status = str((mirrored.get("entry_order") or {}).get("status") or "")
                if entry_status != "filled":
                    mirrored["status"] = "LOCAL_CLOSED_WITHOUT_BROKER_ENTRY_FILL"
                    continue
            if entry_status in TERMINAL_ORDER_STATES:
                mirrored["status"] = f"ENTRY_{entry_status.upper()}"
            else:
                mirrored["status"] = "ENTRY_SUBMITTED"
            continue

        broker_has_position = True if position_symbols is None else symbol in position_symbols

        if config.submit_orders and mirrored.get("exit_order"):
            mirrored["exit_order"] = _refresh_order(client, mirrored.get("exit_order"))
        exit_status = str((mirrored.get("exit_order") or {}).get("status") or "")

        if exit_status == "filled":
            _finish_broker_trade(mirrored, local_status == "CLOSED")
            continue

        if position_symbols is not None and not broker_has_position and mirrored.get("exit_order"):
            mirrored["status"] = "BROKER_POSITION_CLOSED_EXTERNALLY"
            mirrored["manual_reconciliation_required"] = True
            mirrored["reconciliation_reason"] = "Broker no longer reports the filled entry position"
            continue

        safety_exit = (
            local_status == "OPEN" and broker_has_position and broker_clock is not None
            and market_open and minutes_left is not None
            and minutes_left <= BROKER_EXIT_BUFFER_MINUTES
        )
        desired_exit = local_status == "CLOSED" or safety_exit
        if not desired_exit:
            mirrored["status"] = "OPEN_FILLED"
            continue

        if position_symbols is not None and not broker_has_position:
            mirrored["status"] = "BROKER_POSITION_CLOSED_EXTERNALLY"
            mirrored["manual_reconciliation_required"] = True
            mirrored["reconciliation_reason"] = "Local wants exit but broker position is absent"
            continue

        if broker_clock is not None and not market_open:
            mirrored["status"] = "EXIT_WAITING_MARKET_OPEN"
            mirrored["reconciliation_reason"] = "Exit required while broker market is closed"
            continue

        terminal_unfilled = bool(exit_status and exit_status in TERMINAL_ORDER_STATES and exit_status != "filled")
        needs_order = not mirrored.get("exit_order") or terminal_unfilled
        if needs_order:
            retry_count = int(mirrored.get("exit_retry_count") or 0)
            retry = mirrored.get("exit_order") is not None
            if retry:
                history = mirrored.setdefault("exit_history", [])
                prior = dict(mirrored["exit_order"])
                if not history or history[-1].get("client_order_id") != prior.get("client_order_id"):
                    history.append(prior)
                retry_count += 1
                mirrored["exit_retry_count"] = retry_count
            action_key = "exit" if not retry else f"exit_r{retry_count}"
            reason = local.get("exit_reason") if local_status == "CLOSED" else "BROKER_EOD_SAFETY"
            actions.append({
                "action": "RETRY_SELL_TO_CLOSE" if retry else "SELL_TO_CLOSE",
                "signal_id": sid, "symbol": symbol,
                "qty": int(local.get("quantity") or mirrored.get("quantity") or 1),
                "local_reference_bid": local.get("exit_bid"), "reason": reason,
                "retry": retry_count,
            })
            if config.submit_orders:
                order = _recover_or_submit(
                    client, signal_id=sid, action=action_key, symbol=symbol,
                    qty=int(local.get("quantity") or mirrored.get("quantity") or 1),
                    side="sell", position_intent="sell_to_close")
                mirrored["exit_order"] = _order_summary(order)
                mirrored["broker_exit_reason"] = reason
                mirrored["status"] = "EXIT_RETRY_SUBMITTED" if retry else "EXIT_SUBMITTED"

        if config.submit_orders and mirrored.get("exit_order"):
            mirrored["exit_order"] = _refresh_order(client, mirrored.get("exit_order"))
            exit_status = str((mirrored.get("exit_order") or {}).get("status") or "")
            if exit_status == "filled":
                _finish_broker_trade(mirrored, local_status == "CLOSED")
            elif exit_status in TERMINAL_ORDER_STATES:
                mirrored["status"] = f"EXIT_{exit_status.upper()}"

    mirror_state.update({
        "version": "options_alpaca_mirror_v0.2",
        "mode": "ALPACA_PAPER_MIRROR",
        "paper_only": True,
        "base_url": PAPER_BASE_URL,
        "mirror_start_utc": config.mirror_start_utc,
        "shadow_capital": config.shadow_capital,
        "submit_orders": config.submit_orders,
        "broker_market_open": market_open if broker_clock is not None else None,
        "broker_minutes_to_close": minutes_left,
        "broker_position_symbols": sorted(position_symbols or []),
        "reconciliation_required": any(
            t.get("status") in {"EXIT_WAITING_MARKET_OPEN", "BROKER_POSITION_CLOSED_EXTERNALLY"}
            or t.get("status", "").startswith("EXIT_") and t.get("status") != "EXIT_SUBMITTED"
            for t in records.values()
        ),
        "updated_at_utc": _now(),
    })
    return mirror_state, actions


def atomic_write_json(path: str | Path, payload: dict[str, Any]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(p)
