from options_system.prospective_collector import market_clock, market_date_from_clock, stock_snapshot, option_chain
from options_system.prospective_decision import build_prospective_research_state
from options_system.snapshot_store import write_immutable_snapshot, append_index
from options_system.cross_market_features import cross_market_features
from options_system.intraday_context import opening_context
from options_system.vix_context import fetch_vix
from options_system.sector_breadth import SECTORS,sector_breadth_features

clock=market_clock()
if not clock.get("is_open",False):
    print("SKIP_MARKET_CLOSED")
    raise SystemExit(0)

market_date=market_date_from_clock(clock)
spy=stock_snapshot("SPY")
qqq=stock_snapshot("QQQ")
iwm=stock_snapshot("IWM")
sector_snaps={s:stock_snapshot(s) for s in SECTORS}
trade=spy.get("latestTrade") or {}
quote=spy.get("latestQuote") or {}
daily=spy.get("dailyBar") or {}
spot=trade.get("p")
if not spot:
    b,a=quote.get("bp"),quote.get("ap")
    if b and a: spot=(b+a)/2
if not spot or spot <= 0:
    raise RuntimeError("No valid contemporaneous SPY price")

open_t=daily.get("o")
if not open_t or open_t <= 0:
    raise RuntimeError("No valid current SPY daily open in snapshot")

research=build_prospective_research_state(
    market_date,float(open_t),"artifacts/o3/O3_OPEN_PATH_H3_PROB_V02.json"
)
chain,filters=option_chain(spot,market_date=market_date)
cross=cross_market_features(spy,qqq,iwm)
spy_intraday=opening_context("SPY",market_date)
vix=fetch_vix()
sectors=sector_breadth_features(sector_snaps)

payload={"schema_version":"o1.4",
         "market_clock":clock,
         "underlying":{"symbol":"SPY","feed":"iex","snapshot":spy},
         "cross_market":{"feed":"iex","snapshots":{"QQQ":qqq,"IWM":iwm},"features":cross},
         "sectors":{"feed":"iex","snapshots":sector_snaps,"features":sectors},
         "vix":vix,
         "intraday_context":{"SPY":spy_intraday},
         "research_state":research,
         "options":{"feed":"indicative","filters":filters,"snapshot":chain}}
path,digest=write_immutable_snapshot(payload,"data/raw/prospective","spy_options")
append_index(path,digest,"data/raw/prospective/index.jsonl")
records=len(chain.get("snapshots",{}))
print(f"SAVED schema=o1.4 contracts={records} vix={vix['current_price']:.2f} o6={research['o6']['decision']} path={path.name} sha256={digest}")
