def split_path_scenarios(scenarios,threshold=.01):
 event=[];non=[]
 for s in scenarios:
  r=float(s["terminal_return"])
  if max(float(s["mfe"]),-float(s["mae"]))>=threshold:event.append(r)
  else:non.append(r)
 return event,non
def mixture_path_weights(p_event,event,non):
 out=[]
 if event:
  w=p_event/len(event);out += [(r,w,"EVENT") for r in event]
 if non:
  w=(1-p_event)/len(non);out += [(r,w,"NON_EVENT") for r in non]
 return out
