# Market State Engine v1 — Capture Layer

## Status
CAPTURE_AND_LABELING

The engine is not yet authorized to train or emit direction.

## Live causal blocks now captured
1. SPY state and existing OPEN-causal O3 probability.
2. SPY option-chain state:
   - ATM IV
   - call/put IV around spot
   - IV skew
   - spread
   - call/put volume
   - put volume share
   - delta/gamma/vega summaries
3. Cross-market state:
   - SPY, QQQ, IWM return from current session open
   - each instrument gap
   - QQQ minus SPY
   - IWM minus SPY
   - breadth counts and dispersion
4. SPY intraday context:
   - premarket return/range/high/low/volume
   - first-five-minute return/range/high/low/volume
5. Snapshot dynamics:
   - change from previous snapshot
   - change since first captured snapshot of the day
   for spot, ATM IV, skew, put/call behavior and cross-market features.

## Causality
All state features use information available by the snapshot timestamp.
Deltas never cross decision dates.
Outcome labels are added later only from completed sessions.

## Training guardrail
Market State direction training is blocked until at least:
- 20 distinct H3-labeled decision days
- 5 UP days
- 5 DOWN days

These are minimum engineering guardrails, not sufficient evidence for deployment.
Validation must still compare each feature block incrementally against the frozen baseline.

## Next research blocks
- VIX / volatility-index context
- richer option-chain surface by delta and DTE
- broader sector confirmation
- prospective ablation once enough H3 labels exist

O6 remains research-only and direction remains NOT_SUPPORTED.
