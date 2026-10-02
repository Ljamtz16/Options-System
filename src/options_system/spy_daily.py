import json,os,time
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request,urlopen
BASE="https://data.alpaca.markets/v2/stocks/bars"
def daily_bars(symbol,start,end,feed="iex",retries=6):
 all_rows=[]; token=None; urls=[]
 while True:
  p={"symbols":symbol,"timeframe":"1Day","start":start,"end":end,"limit":10000,"feed":feed}
  if token:p["page_token"]=token
  url=BASE+"?"+urlencode(p);urls.append(url)
  h={"APCA-API-KEY-ID":os.environ["APCA_API_KEY_ID"],"APCA-API-SECRET-KEY":os.environ["APCA_API_SECRET_KEY"]}
  for a in range(retries+1):
   try:
    with urlopen(Request(url,headers=h),timeout=30) as r: payload=json.loads(r.read().decode());break
   except HTTPError as e:
    if a==retries:raise
    time.sleep(max(5,2**a) if e.code==429 else 2**a)
  all_rows.extend(payload.get("bars",{}).get(symbol,[]));token=payload.get("next_page_token")
  if not token:break
 return {"bars":{symbol:all_rows}},urls
def fetch_daily_spy(start,end,feed="iex"):
 p,_=daily_bars("SPY",start,end,feed);vals=p.get("bars",{}).get("SPY",[])
 rows=[{"date":x["t"][:10],"open":x["o"],"high":x["h"],"low":x["l"],"close":x["c"],"volume":x["v"]} for x in vals]
 if len({x["date"] for x in rows})!=len(rows):raise ValueError("Duplicate daily SPY sessions")
 rows.sort(key=lambda x:x["date"])
 return rows
