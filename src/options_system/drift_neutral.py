def center_terminal_returns(scenarios):
 vals=[float(s["terminal_return"]) for s in scenarios]
 if not vals:return []
 mean=sum(vals)/len(vals)
 return [{**s,"terminal_return":float(s["terminal_return"])-mean} for s in scenarios]
def directional_tilt_weights(centered_returns,p_up):
 pos=[x for x in centered_returns if x>0];neg=[x for x in centered_returns if x<0];zero=[x for x in centered_returns if x==0]
 out=[]
 if pos:
  w=p_up/len(pos);out += [(x,w,"UP") for x in pos]
 if neg:
  w=(1-p_up)/len(neg);out += [(x,w,"DOWN") for x in neg]
 if zero:
  # zero mass is left at zero only when no directional samples exist
  residual=max(0.0,1-sum(w for _,w,_ in out));w=residual/len(zero) if zero else 0
  out += [(x,w,"ZERO") for x in zero]
 return out
