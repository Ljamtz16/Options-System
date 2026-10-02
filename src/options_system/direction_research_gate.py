def direction_research_status(validation_delta_brier,validation_delta_logloss,min_delta=0.0):
 supported=validation_delta_brier>min_delta and validation_delta_logloss>min_delta
 return {"supported":supported,"direction_enabled":supported,
 "status":"SUPPORTED" if supported else "NOT_SUPPORTED"}
