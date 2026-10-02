import json
from .direction_model import sigmoid
from .calibration import apply_platt
from .probability_guardrail import conservative_probability
def load_probability_artifact(path):
 with open(path) as f:return json.load(f)
def score_open_features(artifact,feature_row):
 names=artifact["features"];mu=artifact["scaler"]["mean"];sd=artifact["scaler"]["std"];w=artifact["model_weights"]
 x=[(float(feature_row[n])-mu[j])/sd[j] for j,n in enumerate(names)]
 raw=sigmoid(w[0]+sum(a*b for a,b in zip(w[1:],x)))
 cal=apply_platt(artifact["platt"],[raw])[0]
 match=None
 for b in artifact["validation_bins"]:
  if b["lo"]<=cal<(b["hi"] if b["hi"]<1 else 1.0000001):match=b;break
 if match is None:cons=min(cal,.5)
 else:cons=conservative_probability(cal,match["event_rate"],match["n"],30)
 return {"raw":raw,"calibrated":cal,"conservative":cons,"reliability_bin":match}
