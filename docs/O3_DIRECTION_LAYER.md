# O3 Direction Layer — H3 OPEN v0.1

## Question
Can OPEN-available SPY state add directional information beyond historical drift?

Targets tested:
1. P(H3 terminal return > 0)
2. P(UP | abs(H3 terminal return) >= 1%)

H3 is OPEN(t) through CLOSE(t+2). Features use current OPEN gap plus completed-bar information through t-1 only.

## Split
Train through 2021-12-31. Validation 2022-2023. 2024-2026 is already inspected and therefore reported only as secondary diagnostic, not pristine OOS.

## Unconditional direction result
Validation n=501, observed UP 53.29%.
Train baseline P(UP)=59.41%.
Model mean P(UP)=72.85%.
Delta Brier vs baseline = -0.05233.
Delta LogLoss vs baseline = -0.17928.

Result: NOT SUPPORTED.

## Direction conditional on magnitude
Validation n=282, observed UP among >=1% events =53.19%.
Train baseline=63.28%.
Model mean P(UP)=79.60%.
Delta Brier=-0.08146.
Delta LogLoss=-0.38601.

Result: NOT SUPPORTED.

## Decision
The current simple OPEN feature set does not justify CALL-vs-PUT direction. Direction guard must remain NONE for predictive use. O3 magnitude and O5 option mechanics remain separable; O6 stays locked.

Negative result is retained as evidence. Future directional research should test richer causal state/regime features and walk-forward recalibration, not tune on the inspected 2024-2026 period.

## v0.2 Regime-feature ablation

Causal OPEN regime features were added with invariance tests:
- completed-bar returns
- gap at current OPEN
- vol5/20/60
- SMA20/SMA50 distance
- drawdown60
- ATR14
- previous-session range/intraday return
- previous volume ratio

Validation 2022-2023 results versus Train baseline:
- base: delta Brier -0.01445, delta LogLoss -0.03308
- base+trend: -0.04530, -0.15044
- base+volatility: -0.03743, -0.10598
- base+micro context: -0.01401, -0.03244
- all: -0.04506, -0.13791

No feature block is supported.

A discrete causal regime model (gap direction x SMA20 trend x vol20-vs-vol60) with Bayesian-style shrinkage was also tested. Increasing shrinkage alpha from 10 to 160 reduced overfit but did not beat baseline. Best/least-negative Validation at alpha=160: delta Brier -0.00110; delta LogLoss -0.00230.

### v0.2 conclusion
NOT SUPPORTED. Further tuning on the same Validation set is prohibited as evidence. A research gate now requires both Validation delta Brier and delta LogLoss to be positive before directional probabilities can be enabled downstream. Current direction remains NONE and O6 remains locked.

Next distinct hypothesis: OPEN-causal first-touch/path direction, because option payoff depends on trajectory and barrier timing, not only H3 terminal sign.
