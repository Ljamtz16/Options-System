def downside_validation_gate(year_metrics):
 required=("2022","2023")
 ok=all(year in year_metrics and year_metrics[year]["delta_brier"]>0 and year_metrics[year]["delta_logloss"]>0 for year in required)
 return {"supported":ok,"status":"SUPPORTED" if ok else "NOT_SUPPORTED","required_years":list(required)}
