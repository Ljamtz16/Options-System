def open_outcome(rows,i,horizon):
 end=i+horizon-1
 if end>=len(rows):return None
 anchor=float(rows[i]["open"]);path=rows[i:end+1]
 return {"decision_date":rows[i]["date"],"horizon":horizon,"label_end":rows[end]["date"],
 "terminal_return":float(rows[end]["close"])/anchor-1,
 "mfe":max(float(x["high"])/anchor-1 for x in path),
 "mae":min(float(x["low"])/anchor-1 for x in path)}
def open_outcomes(rows,i,horizons=(1,3,5,10)):
 return {h:open_outcome(rows,i,h) for h in horizons}
