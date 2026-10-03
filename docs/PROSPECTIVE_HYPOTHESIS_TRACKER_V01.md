# Prospective Hypothesis Tracker v0.1

## Frozen hypotheses
Frozen on 2026-10-02 after exploratory analysis of that session.
They are research hypotheses, not trading rules.

### CALL_FLOW_REVERSAL_V01
- Symbol: SPY
- Side: CALL
- Horizon: 60 minutes
- Conditions:
  - d_atm_iv_prev > 0
  - d_put_call_iv_skew_prev < 0
  - d_put_call_volume_ratio_1pct_prev > 0

### PUT_SKEW_SHORT_V01
- Symbol: SPY
- Side: PUT
- Horizon: 15 minutes
- Conditions:
  - put_call_iv_skew > 0.0045
  - put_call_volume_ratio_1pct < 1.05

The exact machine-readable specification is stored in
`artifacts/intraday/FROZEN_HYPOTHESES_V01.json`.

## Anti-hindsight rule
The 2026-10-02 session is diagnostic only because the hypotheses were created from it.
Prospective evidence starts strictly after 2026-10-02.
No thresholds may be changed based on future outcomes without creating a new hypothesis version.

## Automated pipeline
After each session:
1. rebuild SPY intraday outcomes from immutable prospective snapshots;
2. join outcomes to contemporaneous Market State rows;
3. mark which frozen hypotheses were active at each snapshot;
4. compute results separately for pre-freeze diagnostic and post-freeze prospective data;
5. produce a daily activation report.

Outputs:
- `data/processed/intraday/spy_intraday_outcomes_all_days.csv`
- `data/processed/intraday/prospective_hypothesis_tracker_v01.csv`
- `artifacts/intraday/PROSPECTIVE_HYPOTHESIS_REPORT_V01.json`
- `artifacts/intraday/HYPOTHESIS_DAILY_REPORT_V01.json`

Current prospective sample: 0 rows. This is intentional.


## Contract-path outcomes
The tracker now preserves the representative contract selected at decision time
(0-7 DTE, nearest to absolute 0.50 delta under the existing deterministic selector).
Entry is valued at the contemporaneous ask; later liquidation/path values use observed bid quotes.

For CALL and PUT, the outcomes dataset records:
- selected OCC contract and entry ask;
- conservative returns at 15, 30 and 60 minutes when an eligible future snapshot exists;
- MFE and MAE from observed bid returns along each horizon;
- temporal first-touch state for TP/SL combinations, including TP +10% versus SL -10%.

The frozen hypothesis summary uses each hypothesis' declared horizon:
CALL_FLOW_REVERSAL_V01 uses the 60-minute CALL path and
PUT_SKEW_SHORT_V01 uses the 15-minute PUT path.
TP-before-SL rate excludes paths where neither threshold was reached.
These additions are outcome measurements only; no v0.1 hypothesis threshold was changed.
