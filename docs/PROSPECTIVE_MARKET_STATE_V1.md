# Prospective Market State Dataset v1

## Purpose
Convert immutable live SPY option snapshots into a causal prospective dataset for future Market State / direction research.

## Collector
Windows task: SPY Options Snapshot Collector.
Runs every 5 minutes from 14:15 local time for 9 hours. The collector itself calls Alpaca market clock and stores data only when the US market is open.

Current snapshot schema: o1.2.

## Extracted option-chain features
The v1 extractor uses only fields present in the captured Alpaca option snapshot. It does not fabricate open interest or unavailable fields.

Features include:
- contract_count
- near_atm_count (|moneyness| <= 1%, DTE 1..10)
- atm_iv
- call_iv_1pct
- put_iv_1pct
- put_call_iv_skew
- median_spread_pct_1pct
- call_volume_1pct
- put_volume_1pct
- put_call_volume_ratio_1pct
- put_volume_share_1pct
- median_abs_delta_1pct
- median_gamma_1pct
- median_vega_1pct

## Dataset
Builder:
scripts/build_prospective_market_state.py

Output:
data/processed/prospective/prospective_market_state_v1.csv

Each row preserves capture timestamp, decision date, contemporaneous SPY price, O3 probabilities, Activity Gate, O6 decision and option-chain state.

## Outcome labeling
Labeler:
scripts/label_prospective_market_state.py

Output:
data/processed/prospective/prospective_market_state_labeled_v1.csv

Labels are added only from completed daily sessions. If the market is currently open, the current daily bar is explicitly excluded.

Labels:
- H1 terminal return, MFE, MAE, path >=1%, UP
- H3 terminal return, MFE, MAE, path >=1%, UP
- label_end date

This prevents partial current-session candles from becoming labels.

## Automation
A nightly task rebuilds the dataset and refreshes completed labels. H3 stays blank until three completed sessions exist.

## Research boundary
This dataset is observation/research only. It does not authorize paper or live orders. O6 remains locked behind validated activity, direction, EV, liquidity and stress gates.
