from src.options_system.validation_metrics import auc_rank,calibration_bins
def test_auc_rank(): assert auc_rank([0,0,1,1],[.1,.2,.8,.9])==1
def test_calibration_counts(): assert sum(x["n"] for x in calibration_bins([0,1],[.1,.9]))==2
