from .option_math import black_scholes
def synthetic_chain(spot,dtes=(3,5,7,10),moneyness=(-.02,-.01,0,.01,.02),iv=.20,rate=.04,spread_pct=.08):
 rows=[]
 for dte in dtes:
  for m in moneyness:
   strike=round(spot*(1+m),0)
   for typ in ("call","put"):
    mid=black_scholes(spot,strike,dte/365,rate,iv,typ)["price"]
    spread=max(.01,mid*spread_pct);bid=max(.01,mid-spread/2);ask=max(bid+.01,mid+spread/2)
    rows.append({"symbol":f"SIM-{typ.upper()}-{strike:.0f}-{dte}D","option_type":typ,"strike":strike,"dte":dte,
      "iv":iv,"mid":mid,"bid":bid,"ask":ask,"spread":ask-bid,"source":"SIMULATED"})
 return rows
