def conditional_samples(returns,threshold=.01):
 vals=[float(x) for x in returns if x is not None]
 event=[x for x in vals if abs(x)>=threshold];non=[x for x in vals if abs(x)<threshold]
 return event,non
def mixture_weights(p_event,event_returns,non_event_returns):
 if not 0<=p_event<=1:raise ValueError("p_event")
 e=[float(x) for x in event_returns];n=[float(x) for x in non_event_returns]
 rows=[]
 if e:
  rows += [(x,p_event/len(e),"event") for x in e]
 if n:
  rows += [(x,(1-p_event)/len(n),"non_event") for x in n]
 return rows
