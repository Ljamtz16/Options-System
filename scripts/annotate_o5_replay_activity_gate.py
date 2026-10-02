import json
p="artifacts/o5_o3_integrated_replay_2024-06-03_v03.json"
x=json.load(open(p));pc=x["probability"]["conservative"];x["activity_gate"]={"threshold":0.8,"p_conservative":pc,"activity_pass":pc>=.8,"decision":"RESEARCH_ELIGIBLE" if pc>=.8 else "NO_TRADE_ACTIVITY_GATE"}
open(p,"w").write(json.dumps(x,indent=2));print(json.dumps(x["activity_gate"],indent=2))
