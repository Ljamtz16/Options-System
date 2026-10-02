
# O2 — Underlying Outcome Engine

Status: STARTED

Purpose: estimate measurable future SPY outcomes before mapping them into option P&L.

Initial causal target contract:
- forward returns H1/H3/H5/H10 sessions;
- path MFE and MAE;
- first-touch ordering for symmetric upside/downside barriers;
- unavailable future horizons remain null;
- targets are labels only and must never enter time-t features.

The initial implementation is intentionally independent of option pricing. O3 will estimate probabilities of these outcomes; O4 will translate scenarios into option behavior/P&L.

## O2 Dataset v0.1 — first real build

SPY daily source now uses explicit 1Day bars rather than the existing 1Min helper.
A uniqueness guard rejects duplicate daily sessions.

Feature contract:
- 18 Run10A-methodology features recalculated independently in Options System;
- future-invariance regression test passes;
- long-window features use historical warm-up only.

Real build:
- warm-up source begins 2023-08-01;
- modeling window begins 2024-02-01;
- through 2024-04-30: 62 SPY sessions;
- 62/62 have all 18 features complete;
- 52 currently have complete H10 labels because the final 10 sessions require future observations;
- H1/H3/H5/H10 returns plus MFE/MAE and first-touch labels generated.

No Run10A artifact was modified.

## Event labels v0.2 and first descriptive diagnostic

Added explicit event families for H1/H3/H5/H10:
- |move| >= 1%;
- +0.5% vs -0.5% first touch;
- +1.0% vs -0.5% first touch;
- +0.5% vs -1.0% first touch.
Each first-touch label is UP, DOWN, NEITHER or SAME_SESSION. Incomplete future horizons remain null.

Dataset v0.2:
- 62 sessions, Feb-Apr 2024;
- 62/62 complete 18-feature vectors;
- 52 complete H10 observations;
- 48 total columns.

Descriptive-only H10 findings:
- symmetric +/-0.5%: 28 UP, 24 DOWN, 0 NEITHER among 52 complete observations;
- |move| >=1% within H10: 52/52.
Median-split feature associations were generated only as exploratory diagnostics. The largest observed separation was vol_20, but this is explicitly NOT predictive evidence because the sample is small and no temporal holdout was used.

Next requirement before any predictive claim: expand historical sessions and use frozen temporal train/validation/OOS splits with purge.

## Temporal protocol v0.1

Implemented chronological Train / Validation / OOS splitting with label-end purge.
For horizon H10, an observation is admitted to a partition only when its label_end_h10 is inside that same partition. This prevents labels near a boundary from consuming prices in the next period.

SPY IEX coverage audit:
- requested: 2016-01-01 through 2026-09-01;
- actual returned coverage: 2018-11-01 through 2026-08-31;
- pagination was implemented and re-tested; coverage remained 1,533 sessions.
Therefore the missing earlier history is treated as a source/feed coverage limitation, not silently replaced by another feed.

Initial protocol compatible with available data:
- warm-up begins from actual 2018-11 coverage;
- Train through 2021-12-31;
- Validation 2022-01-01 through 2023-12-31;
- OOS from 2024-01-01 onward;
- purge horizon: 10 sessions.

For H10 +/-0.5% first-touch after feature warm-up/purge:
- Train: n=294, UP=174, DOWN=120, UP rate=59.18%;
- Validation: n=491, UP=257, DOWN=234, UP rate=52.34%;
- OOS: n=658, UP=377, DOWN=281, UP rate=57.29%.

These are base-rate measurements, not model performance.

## Predictive experiment E01 — H10 symmetric first-touch

Target: +0.5% before -0.5% over H10, UP vs DOWN only.
Features: frozen 18-feature causal vector.
Train: through 2021-12-31 with H10 purge.
Validation: 2022-2023 with H10 purge.
OOS: 2024 onward remained unopened for model evaluation.

Implementation:
- deterministic logistic regression implemented locally;
- standardization fit on Train only;
- L2 candidates: 0.001, 0.01, 0.1, 1, 10;
- model selection metric: Validation Brier score, with log-loss and accuracy reported;
- baseline probability is the Train UP rate (59.18%), frozen before Validation.

Validation results:
- baseline: accuracy 52.34%, Brier 0.25413, log-loss 0.70160;
- best logistic candidate (L2=10): accuracy 52.34%, Brier 0.25687, log-loss 0.70735.
All logistic candidates failed to improve the baseline Brier score.

Decision: E01 NOT SUPPORTED. OOS remains unopened for this experiment. No predictive claim is made and this candidate does not advance to O3.

## Predictive sweep E02/E03 — Validation only

A controlled sweep evaluated all existing event families at H1/H3/H5/H10 using the same 18 causal features, Train-only standardization and L2 logistic models. OOS remained unopened.

Direction/trajectory:
- symmetric first-touch failed at H1/H3/H5/H10;
- asymmetric first-touch generally failed;
- up10_dn05_h3 improved only trivially (Brier +0.00019; log-loss +0.00040 vs baseline), treated as insufficient.

Magnitude |move| >= 1%:
- H1: Brier improvement 0.03340; log-loss improvement 0.07704;
- H3: Brier improvement 0.07181; log-loss improvement 0.17220;
- H5: Brier improvement 0.02211; log-loss improvement 0.07584;
- H10: Brier improvement only 0.00117 despite log-loss improvement; event is near-saturated and is not promoted.

Promotion gate v0.1 requires both:
- Brier improvement >= 0.005;
- log-loss improvement >= 0.01.
Candidates passing Validation: abs_gt_1pct_h1, abs_gt_1pct_h3, abs_gt_1pct_h5.

Interpretation: current evidence favors predicting movement magnitude/volatility-like events rather than directional first-touch. This is not yet OOS confirmation and does not authorize trading.

## Stability gate and pre-OOS freeze

Validation was split into 2022 and 2023 without changing the Train-fitted model.

Magnitude H1:
- 2022 delta Brier +0.0594, delta log-loss +0.1313, AUC 0.5555;
- 2023 delta Brier +0.0072, delta log-loss +0.0223, AUC 0.6457.
Status: secondary candidate.

Magnitude H3:
- 2022 delta Brier +0.1286, delta log-loss +0.3207, AUC 0.7126;
- 2023 delta Brier +0.0141, delta log-loss +0.0213, AUC 0.6592.
Status: PRIMARY CANDIDATE.

Magnitude H5:
- 2022 delta Brier +0.0374, delta log-loss +0.1448, AUC 0.6727;
- 2023 delta Brier +0.0064, delta log-loss +0.0052, AUC 0.6602.
Status: held back because 2023 log-loss improvement fails the +0.01 stability threshold.

Frozen pre-OOS contract:
- ID O2-H3-MAGNITUDE-V01
- target abs_gt_1pct_h3
- deterministic L2 logistic, L2=0.1
- 18 fixed features
- Train-only standardization
- Train end 2021-12-31
- Validation 2022-2023
- purge 3 sessions
- no trading threshold selected
- OOS starts 2024-01-01 and remains unopened at freeze time
- contract SHA256 4205db556c9742064d3665bc16a37640d4f3c526509d33e058ed11a0cff8e845

## OOS opening — O2-H3-MAGNITUDE-V01

The frozen H3 magnitude candidate was opened on OOS once, without changing target, features, L2, standardization, split, or threshold policy.

OOS 2024 through available 2026:
- n=665;
- event rate=58.35%;
- frozen Train baseline probability=55.48%;
- baseline Brier=0.24385, model Brier=0.21060, improvement=+0.03325;
- baseline log-loss=0.68082, model log-loss=0.60632, improvement=+0.07450;
- baseline accuracy=58.35%, model accuracy=66.02%;
- AUC=0.71469.

Year stability:
- 2024 n=252: delta Brier +0.02871, delta log-loss +0.06070, AUC 0.7051;
- 2025 n=250: delta Brier +0.05422, delta log-loss +0.12772, AUC 0.7693;
- 2026 n=163: delta Brier +0.00812, delta log-loss +0.01420, AUC 0.6471.

Calibration bins show useful ordering but imperfect extremes. In particular the smallest bin is sparse (n=8), while high-probability predictions average 0.912 vs observed 0.869. Calibration must be treated as a separate requirement before option EV calculations.

Result: O2-H3-MAGNITUDE-V01 is OOS SUPPORTED as a probability-ranking/magnitude-event candidate. This does NOT establish option profitability, direction prediction, or a trading threshold. It may advance to O3 probability-engine hardening.

OOS result SHA256: da6321d996d6cd5fa9ad78b2b19fe52052b0eb5e16c11e69159f94f81794cce2
