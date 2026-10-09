from options_system.session_cache import atomic_text,today
import hashlib
from datetime import datetime,timezone
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


def prospective_rows(source=CURRENT):
    if not source.exists():
        return []

    with source.open(encoding="utf-8", newline="") as fh:
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



def build():
    directory=A/'sessions';directory.mkdir(parents=True,exist_ok=True)
    cache_path=directory/'views-cache.json'
    try:cache=json.loads(cache_path.read_text())
    except (OSError,ValueError):cache={}
    algorithm=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    descriptors={}
    try:
        previous=json.loads((directory/'index.json').read_text())
        descriptors={r['day']:r for r in previous['sessions']}
    except (OSError,ValueError):pass
    sources=sorted((CURRENT.parent/'sessions').glob('????-??-??.csv'))
    if not sources and CURRENT.exists():sources=[CURRENT]
    for source in [*([DISCOVERY] if DISCOVERY.exists() else []),*sources]:
        stat=source.stat();signature=[stat.st_size,stat.st_mtime_ns,algorithm]
        key=str(source.relative_to(ROOT))
        cached=cache.get(key,{})
        if cached.get('signature')==signature and all((directory/(day+'.json')).exists() for day in cached.get('days',[])):continue
        rows=discovery_rows() if source==DISCOVERY else prospective_rows(source)
        groups={}
        for row in rows:groups.setdefault(row['decision_date'],[]).append(row)
        for day,items in groups.items():
            items.sort(key=lambda x:(x.get('symbol') or '',x.get('captured_at_utc') or ''))
            atomic_text(directory/(day+'.json'),json.dumps(items,separators=(',',':')))
            descriptors[day]=dict(day=day,rows=len(items),symbols=sorted({r.get('symbol','SPY') for r in items}),latest_capture=max((r.get('captured_at_utc') or '' for r in items),default=None))
        cache[key]=dict(signature=signature,days=sorted(groups))
    day=today()
    if day not in descriptors:
        atomic_text(directory/(day+'.json'),'[]')
        descriptors[day]=dict(day=day,rows=0,symbols=[],latest_capture=None)
    current=(directory/(day+'.json')).read_text()
    atomic_text(A/'intraday_dashboard_data.json',current)
    atomic_text(A/'intraday_dashboard_data.js','window.DASHBOARD_DATA='+current+';')
    manifest=dict(version=1,today=day,generated_at_utc=datetime.now(timezone.utc).isoformat(),sessions=[descriptors[d] for d in sorted(descriptors)])
    atomic_text(directory/'index.json',json.dumps(manifest,separators=(',',':')))
    atomic_text(cache_path,json.dumps(cache,separators=(',',':')))
    print('DASHBOARD_DATA_OK today',day,'rows',descriptors[day]['rows'],'sessions',len(descriptors))


if __name__=='__main__':build()
