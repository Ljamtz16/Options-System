# SPY Intraday Bootstrap — 2026-10-02

## Source
Only immutable prospective SPY snapshots captured today are used.
No VIX/sector fields are hindsight-filled for times when they were not captured.

Coverage:
- 60 snapshots
- 15:00:04–19:55:05 UTC
- approximately 11:00–15:55 ET
- therefore this is not a full-session sample

## Conservative option convention
Representative near-50-delta contract, shortest available DTE in 0–7.
Entry uses observed ask; exit uses observed bid.
This includes spread cost but not commissions/slippage beyond the quote.

## Aggregate results
15m: CALL mean -2.14%, win rate 41.8%; PUT mean -1.62%, win rate 32.7%.
30m: CALL mean -1.26%, win rate 50.0%; PUT mean -4.74%, win rate 34.6%.
60m: CALL mean -3.71%, win rate 31.9%; PUT mean -7.26%, win rate 21.3%.
EOD: CALL mean -5.08%, win rate 35.6%; PUT mean -22.46%, win rate 3.4%.
## Largest observed opportunities
15m best CALL: +23.21% from 15:55 UTC.
15m best PUT: +58.20% from 15:00 UTC.
30m best CALL: +19.20% from 15:30 UTC.
30m best PUT: +53.28% from 15:00 UTC.
60m best CALL: +27.21% from 15:25 UTC.
60m best PUT: +38.93% from 15:00 UTC.

## Interpretation
Buying a representative CALL or PUT at every checkpoint was negative on average after crossing the quoted spread. However, individual windows produced large positive returns. This supports the project hypothesis that contract selection alone is not enough; a state/direction gate is required.

## Limitations
This is one day, with heavily overlapping windows and only the later part of the session. The observations are correlated and cannot be treated as independent trades or as evidence of a profitable strategy. It is a pipeline-validation/bootstrap dataset only.

Artifacts:
- `artifacts/intraday/SPY_2026-10-02_BOOTSTRAP.json`
- `artifacts/intraday/SPY_2026-10-02_BOOTSTRAP.csv`
