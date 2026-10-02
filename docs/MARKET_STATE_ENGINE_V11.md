# Market State Engine v1.1

## Newly integrated capture blocks

### VIX
Source: Cboe delayed quote JSON for _VIX.
Captured fields:
- current_price
- prev_day_close
- change
- change_pct
- source timestamp

No ETF proxy is used as VIX.

### SPY option surface
Computed from each captured SPY option chain, so it is available retroactively for every existing snapshot whose raw chain is present.

DTE buckets:
- 1-3 days
- 4-7 days
- 8-10 days

For each bucket:
- median call IV
- median put IV
- call/put volume
- 25-delta call/put IV
- 50-delta call/put IV
- 25-delta and 50-delta put-minus-call IV skew
- spread summaries
- contract counts

Delta bands:
- 25d: absolute delta 0.20-0.30
- 50d: absolute delta 0.40-0.60
Nearest-delta fallback is used only if a band is empty.

### Sector breadth
ETFs:
- XLK technology
- XLF financials
- XLE energy
- XLV health care
- XLI industrials

Captured:
- each ETF return from current session open
- count positive/negative
- sector mean return
- dispersion

## Snapshot schema
o1.4 adds raw sector snapshots and delayed Cboe VIX context.
Existing o1.2/o1.3 snapshots remain immutable.

Option-surface features can be reconstructed from older raw option chains.
VIX and sector breadth are intentionally left unavailable for snapshots captured before o1.4 rather than reconstructed with hindsight.

## Research status
CAPTURE_ONLY / NOT_DIRECTION_SUPPORTED.

These blocks are inputs for later incremental ablation tests. They do not alter O6 decisions yet.
