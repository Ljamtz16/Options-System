FEATURE_BLOCKS={
 "baseline":["spot"],
 "premarket":["premarket_return","premarket_range"],
 "open5":["open5_return","open5_range"],
 "vix":["vix_current","vix_change_pct"],
 "cross_market":["market_spy_from_open","market_qqq_from_open","market_iwm_from_open"],
 "sectors":["sector_sector_mean_from_open","sector_sector_dispersion"],
 "options":["atm_iv","put_call_iv_skew","put_call_volume_ratio_1pct",
            "dte_1_3_25d_put_minus_call_iv","dte_1_3_50d_put_minus_call_iv"]}

ORDER=("baseline","premarket","open5","vix","cross_market","sectors","options")

def cumulative_feature_sets():
 out=[];features=[]
 for block in ORDER:
  for f in FEATURE_BLOCKS[block]:
   if f not in features:features.append(f)
  out.append({"through":block,"features":tuple(features)})
 return out

def readiness(rows,min_rows=200,min_days=10):
 days={r.get("market_date") for r in rows if r.get("market_date")}
 return {"ready":len(rows)>=min_rows and len(days)>=min_days,
         "rows":len(rows),"days":len(days),
         "required_rows":min_rows,"required_days":min_days}