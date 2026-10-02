import csv,json
D=list(csv.DictReader(open("artifacts/o5_o3_walkforward_2024_2026_v03.csv")))
def stats(rows):
 r=[float(x["actual_terminal"]) for x in rows]
 return {"n":len(r),"mean_terminal_return":sum(r)/len(r) if r else None,"p_up":sum(x>0 for x in r)/len(r) if r else None,"p_down":sum(x<0 for x in r)/len(r) if r else None}
allrows=D;passes=[x for x in D if x["activity_pass"]=="True"];surv=[x for x in passes if x["best_symbol"]]
out={"all":stats(allrows),"activity_pass":stats(passes),"robust_contract_sessions":stats(surv)}
open("artifacts/o5_o3_walkforward_terminal_bias_v03.json","w").write(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
