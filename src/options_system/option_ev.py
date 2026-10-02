def magnitude_ev(p_move,up_pnl,down_pnl,flat_pnl,directional_up_weight=0.5):
 if not 0<=p_move<=1:raise ValueError("p_move")
 if not 0<=directional_up_weight<=1:raise ValueError("directional_up_weight")
 p_up=p_move*directional_up_weight;p_down=p_move*(1-directional_up_weight);p_flat=1-p_move
 return {"p_up":p_up,"p_down":p_down,"p_flat":p_flat,
 "expected_pnl":p_up*up_pnl+p_down*down_pnl+p_flat*flat_pnl}
def conservative_magnitude_ev(p_raw,p_calibrated,p_conservative,up_pnl,down_pnl,flat_pnl):
 vals={}
 for name,p in (("raw",p_raw),("calibrated",p_calibrated),("conservative",p_conservative)):
  vals[name]=magnitude_ev(p,up_pnl,down_pnl,flat_pnl)
 return vals
