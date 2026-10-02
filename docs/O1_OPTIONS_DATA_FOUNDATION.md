# O1 — Options Data Foundation

Date opened: 2026-10-01
Status: IN PROGRESS

## Objective
Build a point-in-time, auditable data foundation for SPY options research.

## Required information
For each observable contract/time: symbol, option type, strike, expiration, DTE, bid, ask, mid/spread, underlying SPY price and timestamps.
When legitimately available at that time: IV, delta, gamma, theta, vega, volume and open interest.

## Historical-data rule
Current-chain capability does not prove historical-chain capability. O1 must explicitly verify historical bars, trades, quotes, expired-contract discovery and historical Greeks/IV before choosing the storage/reconstruction design.

## Data integrity
Raw provider responses must be preserved without silent overwrite.
Derived fields must be reproducible from raw inputs.
No future contract selection, future quote, future IV/Greek or retrospective liquidity knowledge may enter a prior timestamp.
Provider/feed, request parameters, retrieval timestamp and coverage must be recorded.

## O1 exit criteria
1. Verified provider capability matrix.
2. Frozen canonical option schema.
3. Raw snapshot convention and metadata contract.
4. At least one reproducible SPY options ingestion sample.
5. Integrity/causality tests passing.

## Implementation checkpoint — 2026-10-01

Historical REST client implemented at src/options_system/alpaca_history.py.
Probe entry point implemented at scripts/probe_alpaca_option_history.py.

Security behavior:
- Reads APCA_API_KEY_ID and APCA_API_SECRET_KEY from environment only.
- Does not embed or print credentials.
- Fails closed when either credential is absent.
- Raw JSON snapshot records retrieval timestamp, request URL and SHA-256.

Local credential discovery result:
No Alpaca credential environment variables were present on the laptop.
No reusable .env/config credential file was found under D:\Proyectos\Trading during the scoped check.
Therefore no authenticated historical REST request has been made yet.

Validation:
Full local suite: 7 passed in 0.39s.
Next gate: configure read-capable Alpaca credentials locally, then probe one expired SPY contract for bars and trades.

## Authenticated historical probe — PASSED

Probe date: 2026-10-01
Expired contract: SPY260930C00760000
Historical window: 2026-09-29 14:30:00Z through 15:00:00Z.

Results:
- 1-minute bars: 21 records.
- Individual trades: 64 records.
- Bars fields observed: O/H/L/C, volume, trade count, VWAP, timestamp.
- Trade fields observed: price, size, timestamp, exchange and condition.
- Bars snapshot SHA-256: 9e492d6b758193e6c9d096300d79ebf165fe41f748055cf320932403a6161c1a
- Trades snapshot SHA-256: eaca527cd0eb2219d87cbb8c2a37c2dfcffebf30874513f179b39a33f82dd021

Conclusion:
Historical option bars and trades are AVAILABLE with the configured Alpaca account.
This validates the historical-price backbone for O1. Historical bid/ask quotes and provider-native historical IV/Greeks remain unresolved and must not be assumed.

## Historical quote probe — NOT AVAILABLE on tested endpoint

Tested: 2026-10-01
Request family: /v1beta1/options/quotes
Contract/window: same expired SPY contract and historical interval used for successful bars/trades probes.
Result: HTTP 404 Not Found.

Interpretation:
The same authenticated client succeeds for historical bars and trades, but the analogous historical quotes path is not exposed at this API route.
Therefore historical bid/ask must not be assumed available from Alpaca.
O1 classification for historical quotes: NOT AVAILABLE VIA TESTED ALPACA HISTORICAL API.

## IV/Greeks reconstruction validation — PASSED (initial)

Validation timestamp: 2026-10-01 around 19:57 UTC.
Underlying SPY IEX quote: 763.96 / 763.99.
Contracts: SPY261002C00765000 and SPY261002P00765000.
Option feed: Alpaca indicative.
Assumed annual risk-free rate for parity check: 4.00%.

CALL:
- provider IV 0.161500; derived IV 0.161346.
- provider delta 0.4439; derived 0.4438.
- provider gamma 0.0612; derived 0.0612.
- provider theta -1.3109; derived -1.3098.
- provider vega 0.1580; derived 0.1581.

PUT:
- provider IV 0.153900; derived IV 0.153689.
- provider delta -0.5590; derived -0.5592.
- provider gamma 0.0641; derived 0.0641.
- provider theta -1.1687; derived -1.1640.
- provider vega 0.1578; derived 0.1579.

Interpretation:
The deterministic Black-Scholes/bisection implementation closely reproduces this Alpaca snapshot.
This is an initial validation, not blanket approval for all strikes/DTE/regimes.
Historical reconstructed values remain derived_* and never provider_*.

## Automated prospective collector — ENABLED

Installed: 2026-10-01.
Windows task: SPY Options Snapshot Collector.
State after installation: Ready.
Cadence: every 5 minutes during a broad local daily window; each run checks Alpaca market_clock.
Persistence occurs only when Alpaca reports the US market open.

Universe policy:
- Underlying: SPY.
- Options feed: indicative (until OPRA entitlement is explicitly verified/upgraded).
- Expiration window: 1–10 calendar days forward.
- Strike window: +/-4% around contemporaneous SPY price.
- Maximum chain response: 1000 contracts.
- Stock context feed: IEX.

Operational validation:
Manual run after market close returned SKIP_MARKET_CLOSED and wrote no research snapshot.
Full test suite: 16 passed.

## Historical backfill engine — VALIDATED PILOT

Implemented: 2026-10-01.
Properties:
- paginated retrieval for bars and trades;
- immutable raw page snapshots with SHA-256;
- per-kind manifests;
- checkpoint/resume support;
- completed jobs return their frozen manifest without re-downloading.

Full-session pilot:
Contract: SPY260930C00760000.
Window: 2026-09-29 13:30Z–20:00Z.
Bars: 334 one-minute records, 1 page.
Trades: 1,088 records, 2 pages.
This verifies real pagination beyond the 1,000-record API page limit.

Scale-up rule:
Do not blindly download every listed SPY contract since 2024. Historical universe construction must be point-in-time and bounded by DTE/moneyness/liquidity rules so future contract knowledge cannot leak into selection.

## Historical Universe Builder — VALIDATED CORE

Frozen eligibility rule v0.1:
- SPY only;
- CALL and PUT;
- 1–10 calendar DTE;
- strike within +/-4% of contemporaneous SPY reference price;
- contract status, future close price and future/open-interest outcomes are NOT eligibility inputs.

Discovery detail:
Alpaca's current contract catalog separates already expired contracts as inactive and not-yet-expired contracts as active.
The catalog layer therefore queries both statuses and deduplicates by option symbol.
Status is discovery metadata only and is never an eligibility feature.

Validation session: 2026-09-29, SPY reference 762.08.
Eligible contracts: 976.
Calls: 488. Puts: 488.
Expirations represented: 2026-09-30, 10-01, 10-02, 10-05, 10-06, 10-07, 10-08, 10-09.
Each expiration contributed 122 contracts in this validation slice.
Regression suite: 19/19 passed.

Important historical caveat:
Current catalog discovery can establish contract identity/specifications, but fields such as current status, later close_price and later open_interest must never be treated as point-in-time historical features.

## Historical orchestrator — END-TO-END PILOT PASSED

Implemented: 2026-10-01.
Execution hierarchy: session -> eligible contract -> bars/trades -> per-contract manifests -> session checkpoint.
Completed contracts are skipped on rerun, so the process is safely resumable.

Pilot session: 2026-09-29.
Eligible universe: 976 contracts.
Pilot batch: first 4 contracts.
Result: 4/4 completed, 0 failures.
Rerun: 4/4 recognized as complete; no duplicate downloads.

Observed pilot coverage:
- SPY260930C00732000: 2 bars / 2 trades.
- SPY260930P00732000: 22 bars / 61 trades.
- SPY260930C00733000: 0 bars / 0 trades.
- SPY260930P00733000: 13 bars / 26 trades.

Methodological decision:
Eligibility and observed activity are separate concepts.
A contract remains in the causal eligible universe even if retrospective data later show zero activity.
Future realized volume/trade count must not be used to decide historical eligibility.
Coverage is recorded as an outcome/quality attribute, not a selection feature.

## Automatic historical session builder — VALIDATED

The manual SPY reference has been removed from the historical pipeline.
Each session now obtains its reference from the first available regular-session SPY 1-minute bar (09:30 ET), using its OPEN and preserving feed/source/timestamp provenance.

DST handling:
Regular US session windows are generated in America/New_York and converted to UTC.
Validated examples:
- winter: 09:30 ET -> 14:30Z;
- summer: 09:30 ET -> 13:30Z.
tzdata is now an explicit project dependency.

Automatic range pilot:
2026-09-28: SPY 768.43, 992 eligible contracts.
2026-09-29: SPY 766.85, 976 eligible contracts.
2026-09-30: SPY 766.46, 868 eligible contracts.
2026-10-01: SPY 764.34, 732 eligible contracts.
2026-10-02: NO_SESSION at execution time; no value fabricated.

Session universe manifests are frozen: rerunning a prepared date must reproduce the same manifest or fail closed on mismatch.
Regression suite: 24/24 passed.

Scale policy:
Historical preparation/backfill will run in bounded monthly chunks with resumable checkpoints, rather than one monolithic 2024-2026 job.

## Automatic historical session construction — VALIDATED

Implemented: 2026-10-01.
The manual SPY reference has been removed from the session-building path.
Historical SPY uses the IEX stock-bars endpoint, separate from the options endpoint.
Frozen causal reference v0.1: open of the first available 1-minute SPY bar at the session start timestamp.

Three-session validation:
- 2026-09-25: SPY 768.70 at 13:30:00Z; 744 eligible contracts.
- 2026-09-28: SPY 768.43 at 13:30:00Z; 992 eligible contracts.
- 2026-09-29: SPY 766.85 at 13:30:00Z; 976 eligible contracts.

Frozen manifests:
Session universes are written once. A later attempt that differs from an existing manifest raises Frozen universe mismatch rather than silently rewriting research history.
Validation therefore used a new versioned manifest directory after older pilot manifests correctly triggered this guard.

Regression suite: 26/26 passed.

## Five-session market-data pilot — PASSED

Pilot week: 2026-09-21 through 2026-09-25.
Each session froze the full causal eligible universe and downloaded bars+trades for a 20-contract execution sample.

Results:
- Eligible universes by day: 976, 992, 868, 732, 744.
- Sampled contracts: 100 total.
- Contracts with bars: 95/100.
- Contracts with trades: 95/100.
- Total bars: 2,399.
- Total trades: 7,615.
- Download failures: 0.
- Runtime: 78.71 seconds total (~15.74 sec/session for 20 contracts).
- Pilot raw footprint: 3,220,604 bytes across 611 files.

Scaling decision v0.1:
The full causal universe manifest is always preserved.
One-minute option bars become the primary broad historical backfill layer.
Tick trades are retained as a separate/selective validation layer rather than blindly downloaded for every eligible contract/session.
This is a storage/execution architecture decision, not a retrospective eligibility filter.
Zero-activity contracts remain represented in the universe and coverage metrics.

Added resumable bars-only backfill path.
Regression suite: 27/27 passed.

## Production backfill launch — 2024-02

The real bars-only historical backfill was launched beginning 2024-02.
The initial sequential implementation was intentionally stopped after confirming restart safety because full-session throughput was too low.

A bounded concurrent implementation was then tested:
- 6 workers materially improved throughput;
- API HTTP errors appeared under that pressure;
- execution was stopped rather than accepting missing data;
- production concurrency was reduced to 3 workers;
- HTTP retry with exponential backoff was added;
- interrupted-page FileExists conditions are handled as resume conditions;
- session checkpoints continue to preserve completed symbols.

No eligibility rules changed. This is execution-layer optimization only.
Regression suite after the change: 27/27 passed.

## February 2024 production backfill — execution findings

Production download was resumed and repaired successfully:
- 2024-02-01: 468/468 complete.
- 2024-02-02: repaired to 432/432 complete.
- 2024-02-05: 592/592 complete.
- 2024-02-06: 606/606 complete.
- 2024-02-07: 540/540 complete.
- 2024-02-08: repaired to 470/470 complete.
- 2024-02-09 reached at least 400 completed contracts before the execution strategy was paused for optimization.

Observed provider constraint:
HTTP 429 Too Many Requests is the dominant scaling bottleneck. Failed requests are not interpreted as missing market data.

Resume optimization:
Existing frozen universe manifests are now returned locally without re-querying SPY or the contract catalog.
SPY historical requests now retry 429 responses with exponential backoff.

Batch experiment:
A multi-symbol historical bars engine was implemented and tested.
A real 20-contract query completed as one logical batch and produced one raw page (~122 KB).
The batch engine is immutable, paginated and checkpointed.
A full-session batch experiment confirmed that pagination/rate limits, rather than local CPU, are the principal throughput constraint.

Regression suite: 28/28 passed.

## Historical Downloader v1.0 — batch validation

Implemented batch architecture:
- up to 100 option symbols per logical batch;
- historical bars page limit 10,000;
- next_page_token pagination;
- immutable raw page snapshots;
- checkpoint per completed batch;
- bounded retry/backoff for HTTP 429;
- 0.5 second pacing between completed batches.

Real validation, 2024-02-09:
- frozen universe: 400 contracts;
- completed: 400/400 in 4 batches;
- runtime: 29.82 seconds;
- raw pages: 6;
- bar records: 38,595;
- symbols with observed bars: 339;
- causally eligible symbols with zero observed bars: 61;
- unexpected symbols: 0.

Zero-activity symbols remain part of the frozen universe and are not retrospectively removed.

Additional production run:
- 2024-02-01: 468 contracts, 5 batches, completed in 33.64 seconds.
- 2024-02-02: all 5 batches were checkpointed before the run was stopped while diagnosing inter-session rate-limit waiting.

The batch data path is validated. Remaining production hardening is explicit rate-limit telemetry/pacing between sessions.
Regression suite: 28/28 passed.

## Historical Downloader v1.0 — FROZEN AFTER FULL MONTH

Full production validation: February 2024.

Outcome:
- 20 actual market sessions processed.
- 2024-02-19 correctly skipped because no contemporaneous SPY bar was available (US market holiday).
- 10,374 eligible contract-session observations.
- 8,133 contract-session observations with bars.
- 152 immutable raw batch pages.
- 873,996 one-minute option-bar records.
- 0 unexpected symbols.
- Raw downloader footprint: 186,722,323 bytes (~178.1 MiB).

Production contract:
- frozen causal universe per session;
- up to 100 symbols per batch;
- limit=10,000 datapoints/page;
- page-token pagination;
- immutable raw JSON pages;
- checkpoint per completed batch;
- explicit batch progress telemetry;
- retry/backoff for HTTP 429;
- one-second pacing between batches;
- eight-second pacing between sessions;
- provider/API failures are never converted into market-data missingness;
- causally eligible zero-activity contracts remain in the universe.

Historical Downloader v1.0 is now frozen for the bars backfill unless a documented defect requires a version change.
Regression suite: 28/28 passed.

## Multi-month orchestration — ACTIVE

Added provider-calendar-driven month orchestration.
Alpaca market calendar is now the source of valid trading dates and session open/close times.
Session times are converted from America/New_York to UTC using zoneinfo, so DST and early-close dates are not hard-coded.

Validation:
- 2024-02-01 09:30 New York -> 14:30Z.
- 2024-03-11 09:30 New York -> 13:30Z.
- March 2024 production launch succeeded.
- 2024-03-01: 496/496 symbols checkpointed in 5/5 batches.
- 2024-03-04: 7/7 batches checkpointed and orchestration continued.

This replaces weekday guessing and fixed UTC session windows for future months.

## Quality Gate v1 — implemented

Quality Gate v1 now runs after raw acquisition and before a session is accepted for modeling.

Checks:
- non-empty causal universe;
- raw batch pages exist;
- non-empty universe with zero returned bars => QUALITY_FAIL;
- unexpected symbols;
- duplicate (option_symbol, timestamp) rows;
- explicit coverage counts.

Real validation:
- February 2024: 19 PASS, 1 QUALITY_FAIL.
- March 2024: 20 PASS, 0 FAIL.
- 2024-02-02 is the failed session.

Provider inconsistency evidence for 2024-02-02:
- direct historical bars queries returned zero bars for sampled eligible contracts;
- historical trades for the same contracts/window returned actual executions (including 10 trades for SPY240205C00471000 and 1 trade for SPY240208C00474000).
Therefore 2024-02-02 is not classified as a zero-activity market session. It is classified as missing/inconsistent provider bars and is excluded from bars-based modeling until separately resolved.
No synthetic OHLC and no forward fill are permitted.

Normalization v1:
- canonical per-minute option rows;
- timestamp, symbol, type, strike, expiration, DTE, causal spot reference, OHLC, volume, trade_count, VWAP;
- duplicate symbol/timestamp rows rejected;
- March 2024 normalized raw-to-processed count: 914,527 -> 914,527.

## Integrated processed pipeline v1

The post-acquisition path is now:
raw immutable pages -> Quality Gate v1 -> normalization -> processed monthly manifest.

A QUALITY_FAIL session is not emitted into the modeling dataset.
March 2024 reproduction validation:
- 20 sessions;
- 20 PASS / 0 FAIL;
- 914,527 raw bar rows;
- 914,527 processed rows.
This establishes count-preserving raw-to-processed transformation for the validated month.

April 2024 acquisition was launched using the provider calendar and frozen Downloader v1.0.
