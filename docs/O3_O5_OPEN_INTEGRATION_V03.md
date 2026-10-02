# O3 -> O4/O5 OPEN Integration v0.3

The integrated replay now consumes the frozen O3 OPEN probability artifact rather than an expanding historical event frequency.

Probability chain:
OPEN-causal features -> raw logistic probability -> Platt calibrated probability -> reliability-bin conservative probability.

The event is exactly aligned across layers:
O3 target = max(MFE_H3,-MAE_H3)>=1%.
O5 EVENT/NON_EVENT buckets use the same path definition.
Contract repricing uses the H3 terminal return within each path-defined bucket.

This fixes the previous mismatch where O5 used abs(terminal_return)>=1% to define EVENT.

## Research activity operating point
Validation-only threshold study:
- p_conservative >=0.5: coverage 88.62%, event rate 90.32%
- >=0.6/0.7: coverage 73.05%, event rate 96.17%
- >=0.8/0.9: coverage 60.08%, event rate 98.67%

Chosen research operating point: p_conservative >=0.8.
This is not production-approved; it is a Validation-derived gate for downstream research.

Already-inspected 2024-2026 diagnostic at >=0.8:
coverage 21.77%, event rate 93.10%.

## Replay 2024-06-03
raw=0.8883, calibrated=0.8377, conservative=0.7394.
The subsequent H3 path event occurred.
Because conservative probability is below 0.8, final activity status is NO_TRADE_ACTIVITY_GATE.

A synthetic 3D CALL still had positive conservative EV, but it is vetoed by the activity gate. This is intentional: positive synthetic contract EV cannot override insufficient model confidence.

## Stress alignment
Robustness now uses the conservative path mixture, H3 elapsed day=3, and IV shocks only. Robust-positive count is therefore comparable to the main conservative EV instead of mixing day 1/2/3 horizons.

Direction remains unsupported. No CALL/PUT authorization follows from this layer. O6 remains locked.
