def quality_flags(row,min_dte=1,max_dte=10,max_spread_pct=.20,min_sample=100):
 flags=[]
 if not min_dte<=row["dte"]<=max_dte:flags.append("DTE_OUT_OF_SCOPE")
 if row.get("bid") is None or row.get("ask") is None or row["bid"]<0 or row["ask"]<=0 or row["ask"]<row["bid"]:flags.append("INVALID_QUOTE")
 else:
  mid=(row["bid"]+row["ask"])/2
  if mid<=0 or (row["ask"]-row["bid"])/mid>max_spread_pct:flags.append("WIDE_SPREAD")
 if row.get("iv") is None or row["iv"]<=0:flags.append("MISSING_IV")
 if row.get("sample_n",min_sample)<min_sample:flags.append("LOW_SAMPLE")
 return flags
def research_eligible(row,**kwargs):return len(quality_flags(row,**kwargs))==0
