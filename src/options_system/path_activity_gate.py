def path_activity_gate(p_neither,baseline_neither,min_reduction=.05):
 reduction=baseline_neither-p_neither
 return {"p_neither":p_neither,"baseline_neither":baseline_neither,"reduction":reduction,
 "activity_supported":reduction>=min_reduction}
