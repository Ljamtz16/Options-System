from options_system.downside_validation_gate import downside_validation_gate
def test_requires_both_years_positive():
 x=downside_validation_gate({"2022":{"delta_brier":.1,"delta_logloss":.1},"2023":{"delta_brier":-.01,"delta_logloss":.01}})
 assert not x["supported"]
def test_passes_only_if_both_metrics_positive_each_year():
 x=downside_validation_gate({"2022":{"delta_brier":.1,"delta_logloss":.1},"2023":{"delta_brier":.01,"delta_logloss":.02}})
 assert x["supported"]
