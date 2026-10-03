# Intraday Feature Lab v0.1

## Status
EXPLORATORY ONLY. The current sample is 60 snapshots from 2026-10-02, one trading session.
Nothing in this lab changes or validates frozen hypotheses H01/H02.

## Dataset
`data/processed/intraday/intraday_feature_lab_v01.csv` joins contemporaneous Market State,
the representative 0-7 DTE ~50-delta CALL/PUT available at each snapshot, contract liquidity,
and future outcomes that are used only as labels.

Added contract features include delta, DTE, bid/ask, relative spread, quote sizes and IV.
Time context includes UTC time and minutes from the regular US open.

## Event labels
For CALL and PUT at 15/30/60 minutes:
- MFE >= +10%;
- TP +10% before SL -10%.

The outcome columns and labels are targets, never eligible predictor features.

## Baselines on 2026-10-02
CALL MFE>=10%: 22.0% / 28.8% / 33.9% at 15/30/60m.
PUT MFE>=10%: 20.3% / 27.1% / 30.5%.
CALL TP10-before-SL10: 16.9% / 22.0% / 23.7%.
PUT TP10-before-SL10: 20.3% / 27.1% / 27.1%.

## Univariate discovery protocol
Candidate thresholds use within-sample quartiles with minimum support of 8 observations.
Ranking by lift is for hypothesis generation only. Absolute price thresholds (for example SPY
price levels) are session-specific context and must not be promoted as general rules.
Future returns, MFE, MAE, labels and frozen-hypothesis activation fields are excluded from predictors.

A candidate H03/H04 may be written only as a new EXPLORATORY specification. It does not enter
the prospective scoreboard until separately frozen under a new version before observing its validation data.
