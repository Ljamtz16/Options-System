import json,os
from datetime import datetime,time,timezone
from zoneinfo import ZoneInfo
from urllib.parse import urlencode
from urllib.request import Request,urlopen
from .env import load_local_env
DATA_URL="https://data.alpaca.markets"

def _get(path,params):
 load_local_env();u=DATA_URL+path+"?"+urlencode(params)
 h={"APCA-API-KEY-ID":os.environ["APCA_API_KEY_ID"],"APCA-API-SECRET-KEY":os.environ["APCA_API_SECRET_KEY"]}
 with urlopen(Request(u,headers=h),timeout=30) as r:return json.loads(r.read().decode())

def minute_bars(symbol,start_et,end_et,feed="iex"):
 p={"symbols":symbol,"timeframe":"1Min","start":start_et.astimezone(timezone.utc).isoformat().replace("+00:00","Z"),
    "end":end_et.astimezone(timezone.utc).isoformat().replace("+00:00","Z"),"limit":10000,"feed":feed}
 x=_get("/v2/stocks/bars",p);return (x.get("bars") or {}).get(symbol,[])

def _summary(bars,prefix):
 if not bars:return {f"{prefix}_available":False}
 o=float(bars[0]["o"]);c=float(bars[-1]["c"]);h=max(float(x["h"]) for x in bars);l=min(float(x["l"]) for x in bars)
 v=sum(float(x.get("v") or 0) for x in bars)
 return {f"{prefix}_available":True,f"{prefix}_return":c/o-1,f"{prefix}_range":h/l-1 if l else None,
         f"{prefix}_high_from_open":h/o-1,f"{prefix}_low_from_open":l/o-1,f"{prefix}_volume":v,
         f"{prefix}_bars":len(bars)}

def opening_context(symbol,market_date):
 z=ZoneInfo("America/New_York")
 pre_s=datetime.combine(market_date,time(4,0),z);pre_e=datetime.combine(market_date,time(9,30),z)
 op_s=pre_e;op_e=datetime.combine(market_date,time(9,35),z)
 pre=minute_bars(symbol,pre_s,pre_e);op5=minute_bars(symbol,op_s,op_e)
 out={};out.update(_summary(pre,"premarket"));out.update(_summary(op5,"open5"))
 return out
