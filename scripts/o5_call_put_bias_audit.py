import json
from options_system.env import load_local_env
from options_system.spy_daily import fetch_daily_spy
from options_system.bias_diagnostics import return_diagnostics,center_returns,invert_returns
from options_system.synthetic_chain import synthetic_chain
from options_system.option_simulator import OptionContract,scenario_pnl
load_local_env();rows=fetch_daily_spy("2018-11-01T00:00:00Z","2026-09-01T00:00:00Z")
rets=[float(rows[j+2]["close"])/float(rows[j]["open"])-1 for j in range(len(rows)-2)]
def best_counts(sample):
 counts={"call":0,"put":0};pos={"call":0,"put":0};spots=[500.0]
 for spot in spots:
  for x in synthetic_chain(spot,dtes=(3,5,7,10),moneyness=(-.02,-.01,0,.01,.02),iv=.20,spread_pct=.08):
   entry=min(x["ask"],x["mid"]+(x["ask"]-x["bid"])*.25);c=OptionContract(x["option_type"],x["strike"],x["dte"],entry,x["iv"])
   vals=[scenario_pnl(c,spot*(1+r),iv=.17,dte=max(0,x["dte"]-3),entry_cost=(entry-x["mid"])*100)["net_pnl"] for r in sample]
   ev=sum(vals)/len(vals);x["_ev"]=ev
  chain=synthetic_chain(spot,dtes=(3,5,7,10),moneyness=(-.02,-.01,0,.01,.02),iv=.20,spread_pct=.08)
 # direct type maxima
 res={}
 for typ in ("call","put"):
  evs=[]
  for x in synthetic_chain(500,dtes=(3,5,7,10),moneyness=(-.02,-.01,0,.01,.02),iv=.20,spread_pct=.08):
   if x["option_type"]!=typ:continue
   entry=min(x["ask"],x["mid"]+(x["ask"]-x["bid"])*.25);c=OptionContract(typ,x["strike"],x["dte"],entry,x["iv"])
   ev=sum(scenario_pnl(c,500*(1+r),iv=.17,dte=max(0,x["dte"]-3),entry_cost=(entry-x["mid"])*100)["net_pnl"] for r in sample)/len(sample);evs.append((ev,x["symbol"]))
  res[typ]=max(evs)
 return res
out={"raw":return_diagnostics(rets),"centered":return_diagnostics(center_returns(rets)),"inverted":return_diagnostics(invert_returns(rets)),
"contract_ev_raw":best_counts(rets),"contract_ev_centered":best_counts(center_returns(rets)),"contract_ev_inverted":best_counts(invert_returns(rets))}
open("artifacts/o5_call_put_bias_audit_v01.json","w").write(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
