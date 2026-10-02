def first_touch_open(rows,i,horizon=3,up=.005,down=.005):
 if i+horizon-1>=len(rows):return None
 anchor=float(rows[i]["open"]);u=anchor*(1+up);d=anchor*(1-down)
 for off in range(horizon):
  h=float(rows[i+off]["high"]);l=float(rows[i+off]["low"])
  hu=h>=u;ld=l<=d
  if hu and ld:return {"label":"AMBIGUOUS_SAME_SESSION","session_offset":off}
  if hu:return {"label":"UP","session_offset":off}
  if ld:return {"label":"DOWN","session_offset":off}
 return {"label":"NEITHER","session_offset":None}
def label_family(rows,i,horizon=3):
 specs={"sym_05":(.005,.005),"up10_dn05":(.01,.005),"up05_dn10":(.005,.01),"sym_10":(.01,.01)}
 return {k:first_touch_open(rows,i,horizon,u,d) for k,(u,d) in specs.items()}
