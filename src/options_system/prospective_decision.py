from datetime import timedelta
from .spy_daily import fetch_daily_spy
from .spy_open_features import spy_open_features
from .open_probability_runtime import load_probability_artifact,score_open_features
from .activity_operating_point import activity_operating_point
from .research_decision_engine import research_decision

def build_prospective_research_state(market_date,current_open,artifact_path):
 start=(market_date-timedelta(days=500)).isoformat()+"T00:00:00Z"
 end=market_date.isoformat()+"T00:00:00Z"
 hist=fetch_daily_spy(start,end)
 hist=[r for r in hist if r["date"]<market_date.isoformat()]
 stub={"date":market_date.isoformat(),"open":float(current_open),"high":float(current_open),"low":float(current_open),"close":float(current_open),"volume":0.0}
 rows=hist+[stub]
 feat=spy_open_features(rows,len(rows)-1)
 if feat is None:raise RuntimeError("Insufficient causal daily history for OPEN features")
 art=load_probability_artifact(artifact_path)
 prob=score_open_features(art,feat)
 activity=activity_operating_point(prob["conservative"],.8)
 decision=research_decision(activity["activity_pass"],False,"NONE",0.0)
 return {"features":feat,"probability":prob,"activity_gate":activity,"direction":{"supported":False,"direction":"NONE","edge":0.0},"o6":decision}
