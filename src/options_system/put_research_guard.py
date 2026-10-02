def put_research_eligibility(activity_pass,direction_supported,direction,p_down,baseline_p_down,ev_conservative,robust,min_edge=.05):
 edge=p_down-baseline_p_down
 eligible=bool(activity_pass and direction_supported and direction=="DOWN" and edge>=min_edge and ev_conservative>0 and robust)
 return {"eligible":eligible,"directional_edge_down":edge,"required_edge":min_edge,
 "status":"PUT_RESEARCH_ELIGIBLE" if eligible else "NO_PUT"}
