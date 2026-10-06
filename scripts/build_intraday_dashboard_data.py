import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / "artifacts" / "intraday"
DISCOVERY = A / "DISCOVERY_DASHBOARD_2026-10-02.json"
CURRENT = ROOT / "data" / "processed" / "intraday" / "intraday_options_v2.csv"

H03_SPY = -0.002140966419266088
H03_IWM = -0.003338055604745982


def f(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def h03(row):
    if row.get("symbol") != "SPY":
        return False
    spy = f(row.get("market_spy_from_open"))
    iwm = f(row.get("market_iwm_from_open"))
    return (
        spy is not None
        and iwm is not None
        and spy <= H03_SPY
        and iwm <= H03_IWM
    )


def discovery_rows():
    if not DISCOVERY.exists():
        return []
    rows = json.loads(DISCOVERY.read_text(encoding="utf-8"))
    for row in rows:
        row.setdefault("symbol", "SPY")
        row.setdefault("session_kind", "DISCOVERY")
        row.setdefault("symbol_from_open", row.get("spy_from_open"))
    return rows


def prospective_rows():
    if not CURRENT.exists():
        return []

    with CURRENT.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))

    data = []
    opens = {}

    for row in rows:
        date = row.get("market_date")
        symbol = row.get("symbol")
        spot = f(row.get("spot"))
        key = (date, symbol)

        if key not in opens and spot not in (None, 0):
            opens[key] = spot
        opening = opens.get(key)

        x = {
            "captured_at_utc": row.get("captured_at_utc"),
            "decision_date": date,
            "session_kind": "PROSPECTIVE",
            "symbol": symbol,
            "spot": row.get("spot"),
            "symbol_from_open": ((spot / opening) - 1.0) if spot is not None and opening else None,
            "spy_from_open": row.get("market_spy_from_open"),
            "iwm_from_open": row.get("market_iwm_from_open"),
            "qqq_from_open": row.get("market_qqq_from_open"),
            "vix_current": row.get("vix_current"),
            "vix_change_pct": row.get("vix_change_pct"),
            "atm_iv": row.get("atm_iv"),
            "put_call_iv_skew": row.get("put_call_iv_skew"),
            "put_call_volume_ratio_1pct": row.get("put_call_volume_ratio_1pct"),
            "put_volume_share_1pct": row.get("put_volume_share_1pct"),
            "median_spread_pct_1pct": row.get("median_spread_pct_1pct"),
            "call_contract": row.get("entry_call_contract"),
            "call_entry_ask": row.get("entry_call_ask"),
            "put_contract": row.get("entry_put_contract"),
            "put_entry_ask": row.get("entry_put_ask"),
            "h03": h03(row),
        }

        for horizon in ("5m", "15m", "30m", "60m", "eod"):
            for side in ("call", "put"):
                x[f"{side}_ret_{horizon}"] = row.get(f"{side}_terminal_return_{horizon}")
                x[f"{side}_mfe_{horizon}"] = row.get(f"{side}_best_return_{horizon}")
                x[f"{side}_mae_{horizon}"] = row.get(f"{side}_worst_return_{horizon}")
                x[f"{side}_{horizon}_tp10_sl10"] = row.get(f"{side}_{horizon}_tp10_sl10")

        data.append(x)

    return data


data = discovery_rows() + prospective_rows()
data.sort(key=lambda x: (
    x.get("decision_date") or "",
    x.get("symbol") or "",
    x.get("captured_at_utc") or "",
))

out = A / "intraday_dashboard_data.json"
js = A / "intraday_dashboard_data.js"
raw = json.dumps(data, separators=(",", ":"))
out.write_text(raw, encoding="utf-8")
js.write_text("window.DASHBOARD_DATA=" + raw + ";", encoding="utf-8")

dates = sorted({x.get("decision_date") for x in data if x.get("decision_date")})
symbols = sorted({x.get("symbol") for x in data if x.get("symbol")})
print("DASHBOARD_DATA_OK", "rows", len(data), "dates", dates, "symbols", symbols)
