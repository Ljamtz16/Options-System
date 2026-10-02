from src.options_system.calibration_metrics import ece
def test_perfect_ece_zero():
 r=ece([0,1],[0,1],bins=2);assert r["ece"]==0
