# O5 Contract Intelligence

## Purpose
Evaluate SPY long CALL and long PUT contracts under the same causal probability/distribution assumptions. O5 is comparison and diagnostics only; it does not authorize a trade.

## Contract card
Each evaluated contract records option type, strike, DTE, entry premium, IV, moneyness, development-sample support, EV under raw/calibrated/conservative event probability, stress cube, robust-positive scenario count and worst stress EV.

## Quality gate v0.1
Research eligibility requires:
- DTE 1-10;
- valid positive bid/ask;
- ask >= bid;
- spread/mid <= 20%;
- positive IV;
- empirical distribution sample >=100.

Failure produces explicit flags rather than imputation.

## Interpretation
A contract with positive theoretical EV is not automatically acceptable. O5 exposes whether the result survives conservative probability, time decay, IV stress and execution assumptions. Contract ranking/selection rules remain unfrozen and no CALL/PUT/NO_TRADE decision is made here.
