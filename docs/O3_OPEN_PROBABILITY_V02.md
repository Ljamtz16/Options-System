# O3 Probability Engine OPEN v0.2

Target: P(max(MFE_H3,-MAE_H3)>=1%) with decision at OPEN(t), horizon t..t+2.

Base logistic model is trained through 2021. Platt calibration is fit on 2022-2023 Validation only. 2024-2026 is reported as already-inspected diagnostic and is not used for model/calibrator selection.

Validation n=501:
- raw Brier 0.093874; calibrated 0.090501
- raw LogLoss 0.298295; calibrated 0.285494
- raw ECE 0.044238; calibrated ECE 0.029477

Calibration improves all three metrics on Validation.

Inspected 2024-2026 diagnostic n=666:
- raw Brier 0.195112; calibrated 0.185997
- raw LogLoss 0.576916; calibrated 0.544379
- raw ECE 0.081978; calibrated ECE 0.032214

Reliability guard uses Validation calibration bins. Bins with n<30 cannot increase confidence and are capped conservatively. For sufficiently populated bins the lower Wilson bound limits downstream probability.

This model estimates magnitude/path activity only. It does not estimate UP/DOWN and cannot authorize CALL/PUT. O6 remains locked. Final predictive confirmation requires a future untouched/prospective period.
