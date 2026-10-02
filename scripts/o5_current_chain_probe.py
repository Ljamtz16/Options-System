import json
from options_system.env import load_local_env
from options_system.prospective_collector import market_clock,stock_snapshot,option_chain
load_local_env();clock=market_clock();s=stock_snapshot();trade=(s.get("latestTrade") or {});q=(s.get("latestQuote") or {})
spot=trade.get("p") or ((q.get("bp",0)+q.get("ap",0))/2 if q.get("bp") and q.get("ap") else None)
out={"clock":clock,"spot":spot,"chain_count":0,"valid_quote_iv":0}
if spot:
 c=option_chain(spot); snaps=c.get("snapshots",c) if isinstance(c,dict) else {}
 out["chain_count"]=len(snaps)
 for sym,x in snaps.items():
  qq=x.get("latestQuote") or {};iv=x.get("impliedVolatility")
  if qq.get("bp",0)>0 and qq.get("ap",0)>=qq.get("bp",0) and iv:out["valid_quote_iv"]+=1
print(json.dumps(out,indent=2))
open("artifacts/o5_current_chain_probe.json","w").write(json.dumps(out,indent=2))
