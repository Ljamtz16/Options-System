def directional_edge_guard(p_up,baseline_p_up,min_edge=.05):
 edge=p_up-baseline_p_up
 return {"p_up":p_up,"baseline_p_up":baseline_p_up,"directional_edge":edge,
 "direction_supported":abs(edge)>=min_edge,
 "direction":"UP" if edge>=min_edge else ("DOWN" if edge<=-min_edge else "NONE")}
