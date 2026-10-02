def ece(y,p,bins=10):
 n=len(y);total=0.0;detail=[]
 for b in range(bins):
  lo=b/bins;hi=(b+1)/bins;ix=[i for i,v in enumerate(p) if v>=lo and (v<hi or b==bins-1)]
  if not ix:continue
  mp=sum(p[i] for i in ix)/len(ix);er=sum(y[i] for i in ix)/len(ix);gap=abs(mp-er)
  total+=len(ix)/n*gap;detail.append({"lo":lo,"hi":hi,"n":len(ix),"mean_p":mp,"event_rate":er,"abs_gap":gap})
 return {"ece":total,"bins":detail}
