# PUT Viability / Drift Correction v0.4

## Counterfactual walk-forward
Applied to the 145 sessions passing the frozen O3 Activity Gate.

Original terminal-return distribution:
- robust CALL sessions: 35
- robust PUT sessions: 0
- mean robust CALL EV: +$28.03

Mean-centered distribution:
- robust CALL sessions: 0
- robust PUT sessions: 0

Sign-inverted distribution:
- robust CALL sessions: 0
- robust PUT sessions: 84
- mean robust PUT EV: +$32.13

Conclusion: the engine is not mechanically biased against PUT. Removing drift removes all robust contracts; reversing direction produces PUTs. The observed CALL concentration is driven by directional content/drift in the empirical terminal-return distribution.

## Directional sensitivity on centered distributions
Counterfactual p_down imposed after mean-centering:
- 50% DOWN: 0/145 robust PUT sessions
- 55% DOWN: 50/145 robust PUT sessions
- 60% DOWN: 145/145 robust PUT sessions
- >=65% DOWN: 145/145

This is sensitivity analysis only, not a learned probability.

## Viable correction
Do not force symmetric CALL/PUT counts. Instead:
1. Use activity model only to decide whether enough movement is expected.
2. Remove unconditional drift from the distribution used for directional contract evaluation.
3. Require a separately validated directional model.
4. PUT requires direction=DOWN, incremental p_down edge >=5 percentage points over its causal baseline, positive conservative EV, and aligned stress robustness.
5. CALL should receive the symmetric rule for UP.
6. Otherwise NO TRADE.

Current directional models are NOT SUPPORTED, so PUT authorization remains off today. The counterfactual shows the architecture can support PUT once a genuine downside edge exists.
