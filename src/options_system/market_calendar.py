import json,os,time
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request,urlopen
from .env import load_local_env
BASE="https://paper-api.alpaca.markets/v2/calendar"
def market_calendar(start,end,retries=6):
    load_local_env(); q=urlencode({"start":start,"end":end})
    h={"APCA-API-KEY-ID":os.environ["APCA_API_KEY_ID"],"APCA-API-SECRET-KEY":os.environ["APCA_API_SECRET_KEY"]}
    for attempt in range(retries+1):
        try:
            with urlopen(Request(BASE+"?"+q,headers=h),timeout=30) as r:return json.loads(r.read().decode())
        except HTTPError as exc:
            if attempt==retries: raise
            time.sleep(max(5,2**attempt) if exc.code==429 else 2**attempt)

def regular_session_utc(session_date):
    from datetime import datetime
    from zoneinfo import ZoneInfo
    ny=ZoneInfo("America/New_York"); utc=ZoneInfo("UTC")
    d=str(session_date)
    a=datetime.fromisoformat(d+"T09:30:00").replace(tzinfo=ny).astimezone(utc)
    b=datetime.fromisoformat(d+"T16:00:00").replace(tzinfo=ny).astimezone(utc)
    return a.isoformat().replace("+00:00","Z"),b.isoformat().replace("+00:00","Z")
