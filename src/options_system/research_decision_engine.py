def research_decision(activity_pass,direction_supported,direction,directional_edge,
 contract_available=False,ev_conservative=None,robust=False,liquidity_ok=False,min_direction_edge=.05):
 if not activity_pass:return {"decision":"NO_TRADE_ACTIVITY","research_candidate":False}
 if not direction_supported or direction not in ("UP","DOWN") or abs(directional_edge)<min_direction_edge:
  return {"decision":"NO_TRADE_DIRECTION","research_candidate":False}
 if not contract_available:return {"decision":"NO_TRADE_NO_CONTRACT","research_candidate":False}
 if not liquidity_ok:return {"decision":"NO_TRADE_LIQUIDITY","research_candidate":False}
 if ev_conservative is None or ev_conservative<=0:return {"decision":"NO_TRADE_EV","research_candidate":False}
 if not robust:return {"decision":"NO_TRADE_STRESS","research_candidate":False}
 side="CALL" if direction=="UP" else "PUT"
 return {"decision":f"RESEARCH_{side}_CANDIDATE","research_candidate":True,"side":side}
