def calibration_bins(y,p,bins=5):
 out=[]
 for b in range(bins):
  lo=b/bins;hi=(b+1)/bins
  ix=[i for i,v in enumerate(p) if (v>=lo and (v<hi or b==bins-1))]
  if ix:out.append({"lo":lo,"hi":hi,"n":len(ix),"mean_p":sum(p[i] for i in ix)/len(ix),"event_rate":sum(y[i] for i in ix)/len(ix)})
 return out
def auc_rank(y,p):
 pos=[p[i] for i,v in enumerate(y) if v==1];neg=[p[i] for i,v in enumerate(y) if v==0]
 if not pos or not neg:return None
 wins=sum(1 if a>b else .5 if a==b else 0 for a in pos for b in neg)
 return wins/(len(pos)*len(neg))
