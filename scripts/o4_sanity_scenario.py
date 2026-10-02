import json
from options_system.option_simulator import OptionContract,symmetric_move_scenarios
from options_system.option_ev import conservative_magnitude_ev
spot=100.0
contracts=[OptionContract("call",100,7,2.0,.20),OptionContract("put",100,7,2.0,.20)]
out=[]
for c in contracts:
 s=symmetric_move_scenarios(c,spot,move_pct=.01,elapsed_days=3,risk_free=.04,iv_shift=0,costs=1.0)
 ev=conservative_magnitude_ev(.80,.75,.65,s["up"]["net_pnl"],s["down"]["net_pnl"],s["flat"]["net_pnl"])
 out.append({"type":c.option_type,"scenarios":s,"ev":ev})
print(json.dumps(out,indent=2))
open("artifacts/o4_sanity_scenario_v01.json","w").write(json.dumps(out,indent=2))
