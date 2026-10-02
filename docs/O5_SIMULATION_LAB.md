# O5 Simulation Lab

## Purpose
Exercise O4/O5 while live executable option-chain data is unavailable. Every generated contract is explicitly source=SIMULATED.

## Synthetic chain v0.1
Grid: CALL/PUT, DTE 3/5/7/10, moneyness -2%/-1%/ATM/+1%/+2%, configurable IV and synthetic spread. Premiums are Black-Scholes theoretical values and therefore are not historical market option prices.

## Replay protocol v0.2
Decision anchor is SPY OPEN. H3 terminal outcome is close of session t+2 relative to open_t. Development distributions use only completed observations available before the replay date.

The simulation baseline probability is expanding historical event frequency and is explicitly NOT the current O3 production model. This isolates the O4/O5 plumbing without claiming predictive performance.

## 2024-06-03 diagnostic replay
- OPEN spot: 529.05
- prior completed development observations: 968
- simulated baseline P(|H3 terminal return|>=1%): 0.50
- conservative simulation probability: 0.45
- subsequently revealed H3 terminal return: +1.0585%

Highest conservative-EV synthetic card was SIM-CALL-518-3D with +$8.68 expected P&L under the simulation assumptions. This is not historical realized option profit: the contract premium, IV and spread are synthetic.

Important limitation: stress-cube robustness and the main EV currently summarize different elapsed-day assumptions. They are diagnostics, not a selection rule. O6 remains locked.

## Walk-forward SPY v0.2

A computationally efficient replay used a rolling 300-observation causal development window and a 20-point conditional-quantile approximation to the empirical EVENT/NON_EVENT distributions.

2024 through 2026-08:
- 666 OPEN replays
- best synthetic contract had positive conservative EV in 219 sessions (32.88%)
- best-card type: 504 CALL / 162 PUT
- positive-EV best cards: 219 CALL / 0 PUT
- realized SPY H3 magnitude-event rate: 41.89%
- mean best-card conservative EV across all sessions: -$11.64

These are NOT historical option returns. Premium, IV and spread are synthetic. The all-CALL positive-EV asymmetry is a diagnostic warning, not evidence that CALLs are superior. It may reflect SPY's historical drift, conditional sample composition and synthetic pricing assumptions. O6 remains locked.

## Multi-asset extension

The O4/O5 mechanics are ticker-agnostic, so QQQ, AAPL, NVDA, TSLA and other liquid optionable underlyings can use the same architecture. However each asset requires its own causal data, feature validation, event threshold, probability calibration, empirical move distribution, IV behavior and liquidity gate. SPY probabilities/thresholds must not be copied blindly.

Initial research thresholds are configuration hypotheses only: SPY 1%, QQQ 1.25%, AAPL 1.5%, NVDA 2%, TSLA 2.5%. They are NOT validated/frozen and must be selected from development data before predictive testing.

## CALL/PUT asymmetry audit v0.1

The 219 positive-EV CALL / 0 PUT result was audited with counterfactual return distributions.

Full H3 OPEN return sample (n=1531):
- mean +0.1562%
- up 57.28%, down 42.72%
- magnitude-event subset: up 57.93%, down 42.07%

Counterfactual best synthetic contract EV at spot=500:
- raw returns: best CALL +$12.27; best PUT -$9.09
- mean-centered returns: best CALL -$22.67; best PUT -$1.73
- sign-inverted returns: best CALL -$17.80; best PUT +$37.74

Interpretation: the simulator responds correctly to direction reversal; no simple CALL-favoring pricing bug was found. Removing unconditional drift removes positive EV on both sides. Therefore the earlier CALL concentration is primarily driven by historical directional drift plus synthetic option assumptions, not a learned directional edge.

Walk-forward by year:
- 2024: actual H3 up 59.92%; positive synthetic EV 53.57%; 135 positive CALL, 0 PUT
- 2025: actual H3 up 59.20%; positive synthetic EV 8.00%; 20 CALL, 0 PUT
- 2026 through Aug: actual H3 up 57.32%; positive synthetic EV 39.02%; 64 CALL, 0 PUT

### Direction guard
O5 now has an explicit directional-edge guard. Historical baseline drift alone cannot count as directional support. A direction requires incremental p_up versus its causal baseline of at least a configurable margin (research default 5 percentage points). Otherwise direction=NONE.

This guard is separate from magnitude prediction. Until a validated directional model exists, positive CALL/PUT EV created mainly by unconditional drift is diagnostic and cannot authorize O6.
