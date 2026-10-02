import json,urllib.request
URL="https://cdn.cboe.com/api/global/delayed_quotes/quotes/_VIX.json"
UA={"User-Agent":"Mozilla/5.0","Accept":"application/json"}
def fetch_vix():
 req=urllib.request.Request(URL,headers=UA)
 with urllib.request.urlopen(req,timeout=20) as r:
  p=json.loads(r.read().decode())
 d=p.get("data") or {}
 cur=d.get("current_price");prev=d.get("prev_day_close")
 if cur in (None,0,"0"):raise RuntimeError("Invalid VIX current_price from Cboe")
 cur=float(cur);prev=float(prev) if prev not in (None,"") else None
 return {"source":"CBOE_DELAYED","timestamp":p.get("timestamp") or d.get("last_trade_time"),
         "current_price":cur,"prev_day_close":prev,
         "change":cur-prev if prev is not None else None,
         "change_pct":(cur/prev-1) if prev else None,
         "raw_last_trade_time":d.get("last_trade_time")}
