import json,os,time
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request,urlopen
BASE="https://data.alpaca.markets/v2/stocks"
def _headers():
    if not(os.getenv("APCA_API_KEY_ID") and os.getenv("APCA_API_SECRET_KEY")): raise RuntimeError("Alpaca credentials are not configured.")
    return {"APCA-API-KEY-ID":os.environ["APCA_API_KEY_ID"],"APCA-API-SECRET-KEY":os.environ["APCA_API_SECRET_KEY"]}
def stock_bars(symbol,start_utc,end_utc,feed="iex",retries=6):
    params={"symbols":symbol,"timeframe":"1Min","start":start_utc,"end":end_utc,"limit":1000,"feed":feed}
    url=BASE+"/bars?"+urlencode(params)
    for attempt in range(retries+1):
        try:
            with urlopen(Request(url,headers=_headers()),timeout=30) as r: return json.loads(r.read().decode()),url
        except HTTPError as exc:
            if exc.code!=429 or attempt==retries: raise
            time.sleep(max(5,2**attempt))
