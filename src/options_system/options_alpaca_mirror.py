from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

PAPER_BASE_URL = "https://paper-api.alpaca.markets"
TERMINAL_ORDER_STATES = {"filled", "canceled", "expired", "rejected", "replaced"}


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


def run_mirror(local_state: dict[str, Any], mirror_state: dict[str, Any], config: MirrorConfig,
               client: AlpacaPaperClient | None = None) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    config.validate(require_start=True)
    client = client or AlpacaPaperClient(config.key_id, config.secret_key)
    records = mirror_state.setdefault("trades", {})
    actions: list[dict[str, Any]] = []

    for local in _local_records(local_state, config.mirror_start_utc):
        sid = str(local["signal_id"])
        status = local.get("status")
        mirrored = records.get(sid)

        if mirrored is None and status == "CLOSED":
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

        if mirrored is None and status == "OPEN":
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
            order = client.submit_option_market(
                symbol=str(local["contract"]),
                qty=int(local.get("quantity") or 1),
                side="buy",
                position_intent="buy_to_open",
                client_order_id=_client_id(sid, "entry"),
            )
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
                "status": "ENTRY_SUBMITTED",
            }
            records[sid] = mirrored

        if mirrored is None:
            continue

        if config.submit_orders and mirrored.get("entry_order"):
            mirrored["entry_order"] = _refresh_order(client, mirrored.get("entry_order"))
        entry_status = str((mirrored.get("entry_order") or {}).get("status") or "")
        if entry_status == "filled":
            mirrored["status"] = "OPEN_FILLED"
        elif entry_status in TERMINAL_ORDER_STATES and entry_status != "filled":
            mirrored["status"] = f"ENTRY_{entry_status.upper()}"

        if status == "CLOSED":
            mirrored["local_exit_time"] = local.get("exit_time")
            mirrored["local_exit_bid"] = local.get("exit_bid")
            mirrored["local_gross_pnl"] = local.get("gross_pnl")
            mirrored["local_net_pnl"] = local.get("net_pnl")
            mirrored["local_exit_reason"] = local.get("exit_reason")

            if entry_status != "filled":
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

            if not mirrored.get("exit_order"):
                plan = {
                    "action": "SELL_TO_CLOSE",
                    "signal_id": sid,
                    "symbol": local.get("contract"),
                    "qty": int(local.get("quantity") or 1),
                    "local_reference_bid": float(local.get("exit_bid") or 0),
                    "reason": local.get("exit_reason"),
                }
                actions.append(plan)
                if config.submit_orders:
                    order = client.submit_option_market(
                        symbol=str(local["contract"]),
                        qty=int(local.get("quantity") or 1),
                        side="sell",
                        position_intent="sell_to_close",
                        client_order_id=_client_id(sid, "exit"),
                    )
                    mirrored["exit_order"] = _order_summary(order)
                    mirrored["status"] = "EXIT_SUBMITTED"

            if config.submit_orders and mirrored.get("exit_order"):
                mirrored["exit_order"] = _refresh_order(client, mirrored.get("exit_order"))
                exit_status = str((mirrored.get("exit_order") or {}).get("status") or "")
                if exit_status == "filled":
                    mirrored["status"] = "CLOSED_FILLED"
                    entry_fill = float(mirrored["entry_order"].get("filled_avg_price") or 0)
                    exit_fill = float(mirrored["exit_order"].get("filled_avg_price") or 0)
                    qty = int(mirrored.get("quantity") or 1)
                    broker_gross = (exit_fill - entry_fill) * 100.0 * qty
                    mirrored["broker_gross_pnl"] = broker_gross
                    mirrored["entry_slippage_vs_local_ask"] = entry_fill - float(mirrored.get("local_entry_ask") or 0)
                    mirrored["exit_slippage_vs_local_bid"] = exit_fill - float(mirrored.get("local_exit_bid") or 0)
                    mirrored["gross_pnl_delta_vs_local"] = broker_gross - float(mirrored.get("local_gross_pnl") or 0)
                elif exit_status in TERMINAL_ORDER_STATES:
                    mirrored["status"] = f"EXIT_{exit_status.upper()}"

    mirror_state.update({
        "version": "options_alpaca_mirror_v0.1",
        "mode": "ALPACA_PAPER_MIRROR",
        "paper_only": True,
        "base_url": PAPER_BASE_URL,
        "mirror_start_utc": config.mirror_start_utc,
        "shadow_capital": config.shadow_capital,
        "submit_orders": config.submit_orders,
        "updated_at_utc": _now(),
    })
    return mirror_state, actions


def atomic_write_json(path: str | Path, payload: dict[str, Any]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(p)
