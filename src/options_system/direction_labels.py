def open_direction_labels(rows,horizon=3):
 out=[]
 end_offset=horizon-1
 for i,r in enumerate(rows):
  if i+end_offset>=len(rows):continue
  op=float(r["open"]);cl=float(rows[i+end_offset]["close"])
  ret=cl/op-1
  out.append({"date":r["date"],"open":op,"terminal_return":ret,"up":1 if ret>0 else 0,
   "label_end":rows[i+end_offset]["date"],"horizon":horizon})
 return out
def expanding_baseline(labels,min_history=100):
 out=[]
 for i,x in enumerate(labels):
  if i<min_history:continue
  hist=labels[:i];p=sum(z["up"] for z in hist)/len(hist)
  out.append({**x,"baseline_p_up":p})
 return out
