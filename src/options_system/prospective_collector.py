import json, os, sys, time
from datetime import date, timedelta
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from .env import load_local_env

DATA_URL="https://data.alpaca.markets"
TRADING_URL="https://paper-api.alpaca.markets"

def _headers():
    load_local_env()
    return {"APCA-API-KEY-ID":os.environ["APCA_API_KEY_ID"],
            "APCA-API-SECRET-KEY":os.environ["APCA_API_SECRET_KEY"]}

def _get(base,path,params=None,retries=2):
    url=base+path
    if params: url += "?"+urlencode(params)
    for attempt in range(int(retries)+1):
        try:
            with urlopen(Request(url,headers=_headers()),timeout=30) as r:
                return json.loads(r.read().decode())
        except HTTPError as exc:
            try:
                body=exc.read().decode(errors="replace")[:1500]
            except Exception:
                body="<unavailable>"
            print(f"ALPACA_HTTP_ERROR code={exc.code} attempt={attempt+1} path={path} body={body}",file=sys.stderr,flush=True)
            retryable=exc.code==429 or 500<=exc.code<=599
            if retryable and attempt<int(retries):
                time.sleep(0.75*(attempt+1))
                continue
            raise
        except (URLError, TimeoutError) as exc:
            print(f"ALPACA_NETWORK_ERROR attempt={attempt+1} path={path} error={exc!r}",file=sys.stderr,flush=True)
            if attempt<int(retries):
                time.sleep(0.75*(attempt+1))
                continue
            raise
    raise RuntimeError("unreachable")

def market_clock():
    return _get(TRADING_URL,"/v2/clock")

def market_date_from_clock(clock):
    return date.fromisoformat(str(clock["timestamp"])[:10])

def stock_snapshot(symbol="SPY",feed="iex"):
    return _get(DATA_URL,f"/v2/stocks/{symbol}/snapshot",{"feed":feed})

def option_chain(spot, dte_min=1, dte_max=10, width_pct=.04,
                 feed="indicative", market_date=None, symbol="SPY"):
    today=market_date or date.today()
    params={"feed":feed,
            "strike_price_gte":round(spot*(1-width_pct),2),
            "strike_price_lte":round(spot*(1+width_pct),2),
            "expiration_date_gte":str(today+timedelta(days=dte_min)),
            "expiration_date_lte":str(today+timedelta(days=dte_max)),
            "limit":1000}
    path=f"/v1beta1/options/snapshots/{symbol}"
    return _get(DATA_URL,path,params),params


def option_latest_quotes(symbols, feed="indicative"):
    """
    Fetch latest bid/ask for exact OCC option contracts.

    Returns Alpaca's raw latest-quotes response.
    """
    if isinstance(symbols, str):
        symbols = [symbols]

    symbols = [str(x).strip() for x in symbols if str(x).strip()]
    if not symbols:
        return {"quotes": {}}

    return _get(
        DATA_URL,
        "/v1beta1/options/quotes/latest",
        {
            "symbols": ",".join(symbols),
            "feed": feed,
        },
    )
