MIN_LABELED_DAYS=20
MIN_DIRECTION_EVENTS=5

def market_state_training_readiness(rows):
 days={}
 for r in rows:
  if str(r.get("h3_up","")).strip() not in ("","None"):
   days[r["decision_date"]]=r
 n=len(days)
 ups=sum(str(r.get("h3_up")).lower()=="true" for r in days.values())
 downs=sum(str(r.get("h3_up")).lower()=="false" for r in days.values())
 reasons=[]
 if n<MIN_LABELED_DAYS:reasons.append("INSUFFICIENT_LABELED_DAYS")
 if min(ups,downs)<MIN_DIRECTION_EVENTS:reasons.append("INSUFFICIENT_DIRECTION_EVENTS")
 return {"ready":not reasons,"labeled_days":n,"up_days":ups,"down_days":downs,"reasons":reasons}
