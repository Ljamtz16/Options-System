from options_system.open_probability_runtime import score_open_features
def test_runtime_scores_and_conservative_not_above_calibrated():
 a={"features":["x"],"scaler":{"mean":[0],"std":[1]},"model_weights":[0,0],"platt":{"a":1,"b":0},
 "validation_bins":[{"lo":.5,"hi":.6,"n":100,"event_rate":.4}]}
 r=score_open_features(a,{"x":1});assert 0<=r["conservative"]<=r["calibrated"]<=1
