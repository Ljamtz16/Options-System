# O3 Downside Layer v0.5

Purpose: find a causal downside signal suitable for PUT research without forcing PUT frequency.

Targets tested:
- MAE_H3 <= -1%
- -0.5% before +0.5%
- -1% before +0.5%

The first-touch downside targets did not beat baseline on Validation.

The MAE<=-1% target initially showed a small aggregate Validation improvement with general OPEN features, but failed 2023 stability.

A distinct downside-specific feature set was then tested:
- negative-return fractions 5/10/20
- downside volatility 5/20/60
- down streak
- drawdowns 20/60
- gap and recent returns
- previous intraday/range
- SMA20/SMA50 distances

Causality tests confirm same-day close/high/low and future mutations cannot alter the OPEN features.

Results for MAE_H3<=-1% with downside-specific features:
- Validation aggregate: delta Brier +0.02319; delta LogLoss +0.04567
- 2022: +0.04902 / +0.09706
- 2023: -0.00275 / -0.00592
- 2024 inspected diagnostic: negative
- 2025 inspected diagnostic: negative
- 2026 inspected diagnostic: negative

Predeclared acceptance requires positive incremental Brier AND LogLoss in both 2022 and 2023. Therefore v0.5 is NOT SUPPORTED.

PUT viability remains architecturally confirmed by counterfactual tests, but predictive PUT authorization remains off. No further tuning on the same Validation period will be accepted as evidence.

Future legitimate paths:
- prospective untouched data
- richer causal intraday features once available
- volatility/market-state inputs available before OPEN
- separate downside model trained with more history/provider coverage
- external causal context added under a new frozen protocol
