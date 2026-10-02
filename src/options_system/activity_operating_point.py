def activity_operating_point(p_conservative,threshold=.8):
 return {"threshold":threshold,"p_conservative":p_conservative,"activity_pass":p_conservative>=threshold,
 "decision":"RESEARCH_ELIGIBLE" if p_conservative>=threshold else "NO_TRADE_ACTIVITY_GATE"}
