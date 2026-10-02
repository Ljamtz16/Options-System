# Prospective Snapshot Protocol

Purpose: build our own point-in-time SPY options history for future replay/simulation.

Each capture is immutable and content-hashed. It records:
- capture UTC time and market-open/closed state;
- contemporaneous SPY quote and its feed;
- option feed and exact chain filters;
- per-contract latest quote/trade, IV and Greeks as returned at capture time;
- missing values exactly as observed.

Simulation rule:
A future replay may use only snapshots whose capture/market timestamps are <= the simulated decision time.
Post-close captures are tagged and cannot stand in for an intraday executable quote.
Zero/invalid bid or ask is preserved and fails the executable-price quality gate.
Provider fields remain distinct from derived fields.

Retention:
Never overwrite or mutate a historical snapshot. New observations create new files and index rows.
The JSONL index is discovery metadata; the immutable JSON snapshot is the source of truth.
