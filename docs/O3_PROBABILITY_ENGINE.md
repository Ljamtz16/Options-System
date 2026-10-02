# O3 Probability Engine

## Objective
Convert OOS-supported underlying events into auditable probabilities suitable for later scenario and expected-value calculations. O3 does not choose CALL/PUT and does not claim option profitability.

## Candidate v0.1
Base predictor: O2-H3-MAGNITUDE-V01.
Target: absolute SPY close-to-reference move >=1% within 3 sessions.

## Calibration protocol
Base model is fit on Train only. Calibrators are fit and selected on Validation only. OOS is confirmation, never calibrator selection data.

Validation selected Platt scaling:
- a=0.6483233328
- b=0.2267718181
- raw Brier 0.15147 -> Platt 0.14833
- raw log-loss 0.46731 -> Platt 0.45139

OOS confirmation:
- n=665
- AUC unchanged at 0.71469
- raw Brier 0.21060; Platt Brier 0.21065 (no improvement)
- raw log-loss 0.60632; Platt log-loss 0.60339 (small improvement)
- Platt mean probability 0.61973 vs observed event rate 0.58346.

Conclusion: Platt is the Validation-selected calibrator, but OOS calibration is not yet considered solved. Ranking/discrimination remains supported; probabilities require further reliability diagnostics before O4 EV use.

## Reliability Gate v0.1

ECE (10 equal-width bins):
- Validation raw: 0.05516
- Validation Platt: 0.01927
- OOS raw: 0.03881
- OOS Platt: 0.04177

OOS yearly ECE raw / Platt:
- 2024: 0.06696 / 0.06303
- 2025: 0.06046 / 0.07084
- 2026: 0.08497 / 0.08795

Conclusion: Platt substantially improves Validation calibration but does not improve aggregate OOS ECE. It remains the Validation-selected calibration transform, not proof of perfectly calibrated OOS probabilities.

OOS Platt reliability highlights:
- 0.4-0.5: mean p 0.456, observed 0.396 (n=134)
- 0.5-0.6: mean p 0.547, observed 0.476 (n=189)
- 0.6-0.7: mean p 0.649, observed 0.649 (n=114)
- 0.7-0.8: mean p 0.753, observed 0.713 (n=80)
- 0.8-0.9: mean p 0.847, observed 0.875 (n=64)
- 0.9-1.0: mean p 0.951, observed 0.939 (n=49)

## Conservative probability policy for O4

O4 must not treat the point estimate as unquestioned truth. For EV research it will carry at least:
1. p_raw — frozen base-model probability;
2. p_calibrated — Validation-selected Platt probability;
3. p_conservative — a non-increasing guardrail probability.

The guardrail implementation uses a lower Wilson reliability bound when a reliability bin has sufficient support (minimum n=30); sparse/unsupported bins are capped conservatively. It can only reduce confidence, never increase it.

Important: OOS observations are diagnostics, not calibration-training data. The final production reliability table used prospectively must be learned from permissible historical development data, not retrofitted to maximize OOS performance.

O3 status: ranking SUPPORTED; probability calibration PARTIALLY SUPPORTED; conservative EV interface REQUIRED before O4.
