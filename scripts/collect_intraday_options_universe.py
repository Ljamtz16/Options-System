from options_system.intraday_universe import (
    INTRADAY_UNIVERSE, INTRADAY_CHAIN_DTE_MIN,
    INTRADAY_CHAIN_DTE_MAX, INTRADAY_CHAIN_WIDTH_PCT)
from options_system.prospective_collector import (
    market_clock, market_date_from_clock, stock_snapshot, option_chain)
from options_system.snapshot_store import write_immutable_snapshot, append_index
from options_system.vix_context import fetch_vix
from options_system.sector_breadth import SECTORS,sector_breadth_features
from options_system.cross_market_features import cross_market_features

clock=market_clock()
if not clock.get("is_open",False):
    print("SKIP_MARKET_CLOSED")
    raise SystemExit(0)

market_date=market_date_from_clock(clock)
records={}
errors={}

for symbol in INTRADAY_UNIVERSE:
    try:
        snap=stock_snapshot(symbol)
        trade=snap.get("latestTrade") or {}
        quote=snap.get("latestQuote") or {}
        spot=trade.get("p")
        if not spot:
            b,a=quote.get("bp"),quote.get("ap")
            if b and a: spot=(b+a)/2
        if not spot or spot<=0:
            raise RuntimeError("No valid spot")
        chain,filters=option_chain(
            float(spot),dte_min=INTRADAY_CHAIN_DTE_MIN,
            dte_max=INTRADAY_CHAIN_DTE_MAX,
            width_pct=INTRADAY_CHAIN_WIDTH_PCT,
            market_date=market_date,symbol=symbol)
        records[symbol]={"spot":float(spot),"stock_snapshot":snap,
                         "option_filters":filters,"option_snapshot":chain}
    except Exception as exc:
        errors[symbol]=f"{type(exc).__name__}: {exc}"

sector_snaps={s:stock_snapshot(s) for s in SECTORS}
global_context={"vix":fetch_vix(),
                "sectors":sector_breadth_features(sector_snaps)}
if all(s in records for s in ("SPY","QQQ","IWM")):
    global_context["cross_market"]=cross_market_features(
        records["SPY"]["stock_snapshot"],records["QQQ"]["stock_snapshot"],
        records["IWM"]["stock_snapshot"])

payload={"schema_version":"intraday_o1.1","market_clock":clock,
         "market_date":str(market_date),"universe":list(INTRADAY_UNIVERSE),
         "global_context":global_context,"symbols":records,"errors":errors}
path,digest=write_immutable_snapshot(payload,"data/raw/intraday","intraday_options")
append_index(path,digest,"data/raw/intraday/index.jsonl")
contracts=sum(len((x["option_snapshot"] or {}).get("snapshots",{})) for x in records.values())
print(f"SAVED symbols={len(records)} contracts={contracts} errors={len(errors)} path={path.name}")
