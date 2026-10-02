def regime_key(base,reg):
 trend="UP" if reg["sma20"]>0 else "DOWN"
 gap="UP" if base["gap"]>0 else "DOWN"
 vol="HIGH" if reg["vol20"]>reg["vol60"] else "LOW"
 return gap,trend,vol
def fit_regime_table(rows,alpha=40):
 global_p=sum(x["up"] for x in rows)/len(rows);tab={}
 for x in rows:
  k=x["regime"];a=tab.setdefault(k,[0,0]);a[0]+=x["up"];a[1]+=1
 return {"global_p":global_p,"alpha":alpha,"table":{str(k):(s+alpha*global_p)/(n+alpha) for k,(s,n) in tab.items()}}
def predict_regime(model,key):return model["table"].get(str(key),model["global_p"])
