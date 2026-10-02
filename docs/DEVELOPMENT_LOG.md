# Development Log

## 2026-10-01
- Created isolated Options System project.
- O0 contract frozen: SPY, long CALL/PUT, NO_TRADE default, execution disabled.
- Created Python 3.12.10 virtual environment.
- O0 tests passed 4/4.
- Opened O1 Options Data Foundation.
- Verified expired SPY contract discovery through Alpaca.
- Added safe local .env loader; secrets are ignored by Git and never documented.
- Full suite reached 8/8 tests.
- Authenticated historical Alpaca probe succeeded for expired SPY option.
- Retrieved 21 one-minute bars and 64 trades for a 30-minute historical window.
- Raw probe snapshots saved with SHA-256 provenance.

- Historical option quotes probe returned HTTP 404; bid/ask history is not assumed available.
- Confirmed current Alpaca option snapshots provide latest quote plus IV/Greeks.
- Implemented deterministic Black-Scholes and bisection IV solver without external numerical dependency.
- Full test suite reached 12/12.
- Initial live-snapshot validation closely matched Alpaca IV, Delta, Gamma, Theta and Vega for SPY 765 call/put expiring 2026-10-02.
- Architecture frozen: historical bars/trades + derived Greeks; prospectively capture provider bid/ask/IV/Greeks.

- Implemented prospective SPY option-chain collector.
- Collector refuses persistence while Alpaca market clock is closed.
- Universe bounded to 1-10 DTE and +/-4% spot, indicative feed.
- Added immutable capture store collision protection; regression suite 16/16.
- Installed Windows Scheduled Task 'SPY Options Snapshot Collector' at 5-minute cadence; state Ready.

- Added paginated historical backfill engine with immutable pages, manifests and checkpoint/resume.
- Full-session pilot on SPY260930C00760000 returned 334 1-minute bars and 1,088 trades across 2 trade pages.
- Regression suite remains 17/17.
- Historical scale-up is gated on causal universe construction rather than bulk-downloading every contract.

- Implemented Historical Universe Builder v0.1 with frozen 1-10 DTE / +/-4% spot rules.
- Added explicit leakage guard: close price, open interest and current status do not determine eligibility.
- Historical catalog now merges active+inactive discovery and deduplicates symbols.
- 2026-09-29 validation produced 976 contracts: 488 calls / 488 puts across 8 expirations.
- Regression suite 19/19.

- Added session-level historical orchestrator with restart-safe checkpoints.
- End-to-end pilot: 4/4 contracts completed, zero failures; rerun skipped completed work.
- Added coverage layer preserving zero-activity contracts rather than retrospectively excluding them.
- Regression suite now 21/21.

- Removed manual SPY spot from historical session construction.
- Added causal SPY reference from first regular-session 1-minute open with provenance.
- Added DST-safe NYSE regular-session UTC conversion; tzdata dependency installed/pinned.
- Automatic multi-session pilot succeeded for Sep 28-Oct 1; Oct 2 correctly returned NO_SESSION at execution time.
- Frozen per-session universe manifests added. Regression suite 24/24.

- Added dedicated historical SPY stock-bars client; option and stock endpoints are now separated.
- Removed manual SPY spot from historical session construction.
- Causal reference v0.1 = first 1-minute SPY bar open at session start.
- Validated 2026-09-25/28/29 automatically: 744 / 992 / 976 eligible contracts.
- Frozen-manifest mismatch guard correctly prevented silent replacement of earlier pilot universes.
- Regression suite: 26/26.

- Completed five-session pilot (2026-09-21..25): 100 sampled contracts, 95 with data, 0 failures.
- 2,399 bars / 7,615 trades; 3.22 MB raw; 78.71 sec total.
- Frozen full eligible universes ranged 732-992 contracts/session.
- Architecture decision: broad history = 1-minute bars; tick trades = separate selective validation layer.
- Added restart-safe bars-only backfill; regression 27/27.

- Started production backfill at 2024-02.
- Sequential path confirmed safe but too slow.
- 6-worker trial accelerated throughput but triggered HTTP pressure; stopped intentionally.
- Hardened bars backfill to 3 workers + 4 retries + exponential backoff and interruption-safe resume.
- 27/27 regression tests pass.

- Feb-2024 backfill repaired 2024-02-02 to 432/432 and 2024-02-08 to 470/470.
- 2024-02-01,05,06,07 are also complete; 2024-02-09 reached >=400 contracts before optimization pause.
- Confirmed HTTP 429 as provider scaling bottleneck; never mapped to missing data.
- Resume now reads frozen session manifests locally.
- Added 429 backoff to historical SPY retrieval.
- Added paginated/checkpointed multi-symbol option-bars batch engine.
- Real 20-symbol batch validated; regression suite 28/28.

- Historical Downloader v1 batch path validated.
- 2024-02-09: 400/400 contracts, 4 batches, 6 raw pages, 38,595 bars, 29.82 sec.
- Coverage: 339 symbols with bars, 61 zero-activity eligible, 0 unexpected.
- 2024-02-01: 468 contracts in 33.64 sec.
- 2024-02-02: 5/5 batches checkpointed; run paused to harden inter-session rate-limit telemetry.
- 28/28 tests pass.

- Completed full February 2024 batch backfill.
- 20 market sessions; Feb 19 correctly skipped as no-SPY-bar holiday.
- 10,374 eligible contract-session observations; 8,133 with bars.
- 873,996 1-minute bars across 152 immutable raw pages.
- 0 unexpected symbols; 186,722,323 bytes raw.
- Historical Downloader v1.0 frozen with batch=100, page limit=10,000, 429 backoff, 1s batch pacing, 8s session pacing.

- Added Alpaca market-calendar client for valid sessions and early-close-aware schedules.
- Added DST-safe America/New_York -> UTC conversion; tested Feb EST vs Mar EDT.
- Added resumable month orchestrator using frozen Downloader v1.0.
- March 2024 launched successfully: Mar 1 5/5 batches; Mar 4 7/7 batches; continuing.

- Implemented Quality Gate v1 and month-level quality reports.
- Feb 2024: 19 PASS / 1 QUALITY_FAIL; Mar 2024: 20/20 PASS.
- Diagnosed Feb 2 provider inconsistency: option bars absent while sampled contracts have historical trades.
- Feb 2 excluded from bars-based modeling; no synthetic OHLC/forward-fill.
- Implemented Normalization v1; March preserved all 914,527 raw bars as normalized rows.

- Integrated raw -> Quality Gate -> normalization -> processed monthly pipeline.
- March reproduction: 914,527 raw bars == 914,527 processed rows; 20/20 PASS.
- Launched April 2024 acquisition with provider calendar and Downloader v1.0.
- Started O2 Underlying Outcome Engine: H1/H3/H5/H10 returns, MFE/MAE and first-touch barrier targets; tail labels remain null.

- April 2024 acquisition/processing completed: 22/22 sessions PASS, 1,236,988 processed option bars.
- Corrected O2 SPY source to explicit 1Day bars after a validation run exposed accidental 1Min usage.
- O2 Dataset v0.1 real build: Feb-Apr 2024 = 62 sessions, 62/62 complete 18-feature vectors, 52 H10-labeled.
- Future-invariance and outcome tests pass; Run10A remains untouched.

- O2 event labels v0.2 implemented and tested: magnitude and asymmetric/symmetric first-touch targets across H1/H3/H5/H10.
- O2 dataset now has 48 columns; 62 sessions and 52 complete H10 labels.
- First descriptive diagnostic saved to artifacts/o2/o2_descriptive_v01.json.
- H10 +/-0.5% first-touch observed 28 UP / 24 DOWN; descriptive only, not predictive evidence.
- Predictive claims remain locked pending larger history + temporal validation/OOS with purge.

- Implemented O2 temporal protocol with explicit label_end_horizon purge.
- Audited SPY IEX daily coverage: actual 2018-11-01 to 2026-08-31 despite request back to 2016; pagination confirmed this is not a 10k truncation.
- No silent provider/feed substitution performed.
- Initial split frozen for experimentation: Train <=2021-12-31, Validation 2022-2023, OOS >=2024, H10 purge.
- H10 +/-0.5% base rates: Train 59.18% UP (n=294), Validation 52.34% (n=491), OOS 57.29% (n=658). Baselines only.

- O2 predictive E01 completed on Validation only: H10 +/-0.5% first-touch with 18 causal features and deterministic L2 logistic regression.
- Train-only standardization; Train base probability frozen at 59.18%.
- Validation baseline Brier/logloss = 0.25413 / 0.70160.
- Best logistic (L2=10) = 0.25687 / 0.70735; no improvement.
- E01 NOT SUPPORTED. OOS deliberately remains unopened; candidate does not advance to O3.

- E02/E03 Validation target sweep completed with OOS unopened.
- Directional first-touch targets did not show material Validation improvement.
- Magnitude target |move|>=1% passed promotion gate at H1/H3/H5.
- H3 magnitude strongest Validation improvement: delta Brier +0.07181, delta log-loss +0.17220.
- Added promotion gate: minimum +0.005 Brier and +0.01 log-loss improvement; rejects trivial H3 asymmetric directional gain and near-saturated H10 magnitude.

- O2 magnitude stability gate completed by Validation year.
- H3 passed materially in both 2022 and 2023 and is primary candidate; H1 secondary; H5 held back.
- Frozen pre-OOS contract O2-H3-MAGNITUDE-V01, L2=0.1, 18 fixed features, Train-only standardization, no trading threshold.
- Frozen contract SHA256: 4205db556c9742064d3665bc16a37640d4f3c526509d33e058ed11a0cff8e845.
- OOS remained unopened through the freeze.

- Opened frozen O2-H3-MAGNITUDE-V01 OOS exactly once.
- OOS n=665: Brier 0.21060 vs baseline 0.24385; log-loss 0.60632 vs 0.68082; accuracy 66.02% vs 58.35%; AUC 0.71469.
- Improvement persisted separately in 2024, 2025, and 2026.
- Status: OOS SUPPORTED for magnitude-event probability ranking; no claim of option profitability/direction and no trading threshold.
- Calibration extremes remain imperfect and must be hardened before EV use.
- Result SHA256 da6321d996d6cd5fa9ad78b2b19fe52052b0eb5e16c11e69159f94f81794cce2.

- O3 Probability Engine started from frozen O2-H3-MAGNITUDE-V01.
- Implemented Platt and temperature calibration without external ML dependency.
- Calibrators fit/selected on Validation only; OOS not used for selection.
- Platt selected: Validation Brier 0.15147 -> 0.14833; log-loss 0.46731 -> 0.45139.
- OOS Platt: Brier 0.21065 vs raw 0.21060 (flat/slightly worse), log-loss 0.60339 vs raw 0.60632 (small improvement), AUC unchanged 0.71469.
- OOS mean calibrated p 0.61973 vs event rate 0.58346; calibration not declared solved.
- Added ECE/reliability diagnostic implementation for next O3 hardening step.

- O3 Reliability Gate v0.1 completed.
- Validation ECE raw/Platt 0.05516/0.01927; OOS 0.03881/0.04177.
- Platt improves Validation calibration but not OOS aggregate ECE; calibration status PARTIALLY SUPPORTED.
- High OOS probability bins showed reasonable reliability, while 0.4-0.6 was overconfident.
- Added conservative probability guardrail with Wilson lower bound, minimum reliability-bin n=30, and invariant that conservative p cannot exceed input p.
- O4 interface will carry p_raw, p_calibrated, p_conservative; OOS diagnostics cannot be retrofitted as calibration training.

- O4 Option Simulator v0.1 started.
- Added immutable OptionContract plus Black-Scholes scenario repricing and gross/net P&L with explicit costs.
- Initial test exposed wrong black_scholes argument ordering; fixed and added interface parity regression test.
- Added direction-neutral magnitude EV bridge. A magnitude probability cannot be interpreted as bullish/bearish probability.
- O4 carries raw/calibrated/conservative EV views separately.
- Controlled ATM 7-DTE sanity example with 1% move over 3 days and unchanged IV produced negative EV for both long CALL and long PUT, illustrating theta/premium can overwhelm correct magnitude expectation.
- This sanity scenario is not a market result and not evidence of profitability.

- O4 empirical H3 distribution bridge implemented.
- Added empirical quantiles, standardized nearest-neighbor diagnostics, conditional EVENT/NON_EVENT samples, mixture weights, and weighted option EV.
- k=100 neighbor mean-return OOS MAE 1.12845% vs global Train 1.13886%; improvement too small to promote k-NN as probability model.
- Architecture frozen conceptually: O3 supplies event probability; empirical historical samples supply conditional move-size shape; O4 reprices all weighted samples.
- This removes the assumption that every magnitude event is exactly +/-1% while preserving the distinction between magnitude and direction.

- O4 path/IV/execution hardening v0.3 implemented.
- Added H3 path metrics: terminal return, MFE from highs, MAE from lows, and causal barrier labeling. Same-daily-bar double touches are AMBIGUOUS_SAME_SESSION.
- Added explicit IV stress grid; historical IV is not fabricated because tested Alpaca historical API does not provide it.
- Added executable quote model for prospective long-option entry/exit using bid/ask, fraction-of-spread slippage and fees. Invalid/zero quotes rejected.
- Added return x elapsed-time x IV stress cube to expose theta and volatility sensitivity.
- Historical backtests without quotes remain theoretical-mid research, not executable performance.
- O4 targeted regression: 27 passed.

- O5 Contract Intelligence v0.1 implemented.
- Added per-contract card with raw/calibrated/conservative EV, empirical support, stress cube, robust-positive count and worst stress EV.
- Added quality gate: DTE 1-10, valid bid/ask, spread/mid <=20%, positive IV, empirical sample >=100. Failures are flagged, never imputed.
- Current Alpaca probe was performed while market closed: SPY reference 764.1, chain_count=0, valid quote+IV contracts=0. No stale/fabricated real contract comparison was produced.
- O5 therefore correctly returns no executable research candidates when current chain data is unavailable.

- O5 Simulation Lab implemented with reproducible synthetic SPY option chains and O5 contract-card evaluation.
- Initial close-anchored replay was preserved as diagnostic only after detecting mismatch with the OPEN decision architecture.
- Replay v0.2 corrected anchor to OPEN and uses only pre-decision completed development outcomes.
- 2024-06-03 OPEN replay: spot 529.05, development n=968, simulated event frequency 50%, conservative 45%; subsequently revealed H3 terminal return +1.0585%.
- Highest synthetic conservative-EV card: SIM-CALL-518-3D, +$8.68 expected P&L under synthetic premium/IV/spread assumptions. This is NOT realized historical option profit.
- O6 remains locked; no trade-selection rule inferred from this single replay.

- Audited 219 CALL / 0 PUT positive-EV asymmetry.
- H3 OPEN returns n=1531 had mean +0.1562% and 57.28% positive observations.
- Counterfactual sign inversion flips option preference: raw best CALL +$12.27 / PUT -$9.09; inverted CALL -$17.80 / PUT +$37.74. No simple CALL-favoring pricing bug found.
- Mean-centering removes positive EV from both sides, demonstrating that unconditional drift materially drives the synthetic CALL result.
- Added direction_guard: baseline drift alone cannot constitute directional evidence; research default requires >=5pp incremental directional edge.
- O6 remains locked pending a separately validated directional signal and real/prospective option execution evidence.

- O3 Direction Layer H3 OPEN v0.1 tested.
- Unconditional P(UP): Validation n=501, model loses baseline (delta Brier -0.05233; delta LogLoss -0.17928) and overpredicts UP.
- Conditional P(UP | |H3|>=1%): Validation n=282, also loses baseline (delta Brier -0.08146; delta LogLoss -0.38601).
- Both directional hypotheses marked NOT SUPPORTED. 2024-2026 remains inspected diagnostic only, not pristine OOS.
- direction_guard therefore remains NONE for predictive use; no CALL/PUT authorization and O6 remains locked.

- Direction Layer v0.2 causal regime ablation completed. No feature block beat baseline on 2022-2023 Validation.
- Discrete gap x trend x volatility regimes with shrinkage alpha 10..160 also failed; alpha160 least-negative delta Brier -0.00110 and delta LogLoss -0.00230.
- v0.2 frozen NOT SUPPORTED; no further tuning on same Validation accepted as evidence.
- Added direction_research_gate requiring positive incremental Brier AND LogLoss before downstream direction can be enabled.
- Next distinct research hypothesis is path/first-touch direction rather than terminal H3 sign.

- O3 First-Touch v0.3 implemented using OPEN anchor and HIGH/LOW path over t..t+2.
- Same-session dual barrier touches explicitly AMBIGUOUS_SAME_SESSION.
- Direction among resolved UP/DOWN cases failed baseline for all tested barrier families.
- Absolute-event experiment found non-directional path-activity signal candidates. Strongest: symmetric +/-1% NEITHER, Validation delta Brier +0.05837 and delta LogLoss +0.19652.
- This candidate may support future NO_TRADE/activity gating but does not support CALL/PUT direction.
- Added path_activity_gate; candidate not promoted pending stability and corrected OPEN magnitude integration.

- Rebuilt O2 Magnitude under strict OPEN causality. New 17-feature builder uses completed data through t-1 plus current OPEN only.
- Causality tests pass: same-day close/high/low/volume and future mutations cannot change decision features.
- New OPEN outcomes use inclusive horizons, terminal close return, high/low MFE/MAE and correct label_end.
- Legacy predictive artifacts formally marked SUPERSEDED_DIAGNOSTIC_ONLY.
- Corrected dataset: 1,472 rows from 2020-10-20 to 2026-08-31.
- Old terminal H3 |return|>=1% target failed after correction.
- H1 path +/-1% aggregate support was rejected because 2023 stability failed.
- Frozen research candidate: O2_OPEN_PATH_1PCT_H3_V02_CANDIDATE. Validation delta Brier +0.05456 / LogLoss +0.18377; both 2022 and 2023 individually positive.
- 2024-2026 is already inspected diagnostic only; final confirmation requires future untouched/prospective data. Candidate is magnitude/activity only; no direction and O6 remains locked.

- O3 Probability Engine OPEN v0.2 calibrated the frozen H3 +/-1% path-excursion candidate.
- Platt calibration on 2022-2023 Validation improved Brier 0.093874 -> 0.090501, LogLoss 0.298295 -> 0.285494, ECE 0.044238 -> 0.029477.
- Already-inspected 2024-2026 diagnostics also improved after calibration: Brier 0.195112 -> 0.185997; LogLoss 0.576916 -> 0.544379; ECE 0.081978 -> 0.032214.
- Reliability bins and conservative Wilson lower-bound guard retained; sparse bins n<30 cannot increase confidence.
- Probability remains magnitude/activity only; no directional authorization and O6 remains locked.

- Integrated frozen O3 OPEN probability runtime into O5 synthetic replay.
- Corrected event-definition mismatch: EVENT/NON_EVENT is now path excursion max(MFE,-MAE)>=1%, while option repricing uses terminal H3 return.
- Added reproducible runtime with stored scaler, logistic weights, Platt parameters and reliability bins.
- Validation-derived research activity operating point set at conservative p>=0.8: 60.08% coverage / 98.67% event rate. Inspected 2024-2026 diagnostic: 21.77% / 93.10%.
- Replay 2024-06-03 scored raw .8883, calibrated .8377, conservative .7394; actual path event occurred, but activity gate correctly returns NO_TRADE_ACTIVITY_GATE.
- Stress robustness aligned to conservative mixture and elapsed day 3. Direction remains unsupported; O6 locked.

- Completed frozen O3 -> O5 integrated diagnostic walk-forward over 666 sessions in 2024-2026.
- Activity Gate p_conservative>=0.80 passed 145 sessions (21.77%); actual path-event rate among passes 93.10%.
- 35 sessions had at least one synthetic contract with positive conservative EV robust to aligned IV shocks; 63 robust contracts total.
- Best robust contracts remained CALL 35 / PUT 0. This reduces old 219 CALL-positive sessions to 35 robust gated sessions but does not remove CALL concentration.
- Bias audit: all sessions mean H3 +0.1733% / 59.01% UP; gated sessions +0.4601% / 63.45% UP; robust sessions +0.6119% / 65.71% UP.
- Conclusion: magnitude gate selects states whose empirical terminal-return distribution is more bullish, but this is not validated directional edge. direction_guard remains mandatory and O6 stays locked.

- Completed original vs mean-centered vs sign-inverted drift counterfactual on 145 O3-gated sessions.
- Original: 35 robust CALL / 0 PUT. Centered: 0 / 0. Inverted: 0 CALL / 84 robust PUT, mean PUT EV +$32.13.
- Therefore no mechanical PUT suppression bug was found; CALL concentration is driven by directional drift/content in empirical terminal returns.
- Directional sensitivity on centered distributions: p_down 50% => 0 PUT sessions; 55% => 50/145; 60% => 145/145. This is counterfactual, not evidence of a live DOWN signal.
- Added put_research_guard: activity pass + validated DOWN direction + >=5pp incremental downside edge + positive conservative EV + stress robustness required.
- Current directional layer remains NOT SUPPORTED, so PUT authorization remains off and O6 locked.

- O3 Downside Layer v0.5 completed.
- Tested MAE_H3<=-1%, DOWN first +/-0.5%, and DOWN -1% before UP +0.5%. First-touch downside targets failed Validation baseline.
- Downside-specific causal OPEN features improved aggregate MAE<=-1% Validation (delta Brier +0.02319; LogLoss +0.04567) but failed 2023 stability (-0.00275 / -0.00592).
- Inspected 2024, 2025 and 2026 diagnostics are also negative.
- Frozen O3_DOWNSIDE_V05 as NOT_SUPPORTED. Added year-stability gate requiring positive Brier and LogLoss in both 2022 and 2023.
- PUT remains technically viable but predictively unauthorized. No further tuning on the same Validation period accepted as evidence.

- Implemented O5 drift-neutral utilities: historical terminal returns can be mean-centered before directional reweighting.
- Implemented O6 Research Decision Engine with explicit NO_TRADE reasons and symmetric CALL/PUT research candidate outputs.
- Direction is mandatory: activity alone cannot authorize a side.
- Integrated O3 OPEN research state into prospective collector schema o1.2.
- Prospective snapshots now include causal features, raw/calibrated/conservative activity probability, Activity Gate, direction status and O6 decision.
- Fixed option expiration-date filters to use Alpaca market date from the market clock rather than laptop local date.
- Current directional layer remains NOT_SUPPORTED; collector therefore records NO_TRADE_DIRECTION whenever activity passes.

- Added Prospective Market State Dataset v1.
- Added option-chain feature extractor using only captured provider fields; no synthetic OI or missing data.
- Added causal prospective CSV builder.
- Added H1/H3 outcome labeler that excludes the current daily session while the market is open.
- Updated collector Windows task to every 5 minutes from 14:15 local for 9 hours; Alpaca clock remains the authoritative market-open gate.
- Battery restrictions disabled for the collector task to improve continuity while the laptop is awake.
- Added nightly dataset/label refresh pipeline.

- Upgraded live prospective snapshot schema to o1.3.
- Added contemporaneous QQQ and IWM snapshots and causal cross-market features.
- Added SPY premarket and OPEN+5 minute causal summaries from provider minute bars.
- Added within-day snapshot-delta features; deltas reset each decision date and never cross sessions.
- Added Market State training-readiness guard: minimum 20 H3-labeled days with >=5 UP and >=5 DOWN before direction training can start.
- Direction remains NOT_SUPPORTED; new Market State features are capture/research only.

- Added Cboe delayed VIX context using official delayed quote JSON endpoint; no VIX ETF proxy.
- Added SPY option surface features by DTE buckets 1-3, 4-7 and 8-10 days and by 25d/50d delta bands.
- Fixed delta surface selector after test exposed mixing between 25d and 50d contracts; now explicit delta bands with controlled fallback.
- Added sector breadth capture for XLK, XLF, XLE, XLV and XLI.
- Upgraded prospective schema to o1.4 for future sessions.
- Existing raw snapshots remain immutable. Option surface can be derived from their stored chains; VIX/sector fields are not hindsight-filled for pre-o1.4 snapshots.

- Added Intraday Options Engine v1 as a separate research branch.
- Universe: SPY, QQQ, IWM, AAPL, NVDA, MSFT, AMZN, META, TSLA.
- Added generalized multi-symbol option-chain collector with DTE 0-7 and +/-3% strike window.
- Added intraday outcomes at 5/15/30/60 minutes and EOD.
- Added representative near-50-delta CALL/PUT tracking with conservative ask-entry / bid-exit P&L.
- Added global VIX, cross-market and sector-breadth context to intraday snapshots.
- Registered 5-minute intraday collector and daily dataset-builder Windows tasks.
- Verified all nine underlyings return option-chain data from Alpaca.
- Regression after integration: 35 tests passed. No paper/live order path enabled.

- Closed breakpoint and integrated Intraday Options Engine as official parallel research branch.
- Added Intraday Outcome Engine v2 with MFE/MAE, first-touch ±25/±50 bp and CALL/PUT path outcomes.
- Added direct profit and TP-before-SL targets for option paths.
- Added Contract Selector Lab: 25d/40d/50d/60d across DTE 0, 1, 2-3 and 4-7.
- Added cumulative intraday ablation feature blocks and readiness guard.
- Added automatic daily intraday report and upgraded post-session build to dataset v2.
- Full relevant regression: 38 passed.
- Closed breakpoint and integrated Intraday Options Engine as an official branch alongside swing.
- Added Intraday Liquidity Gate v1 with quote, spread, size and delta checks.
- Added Intraday Research Decision Engine for 15/30/60m with explicit NO_TRADE precedence and research-only CALL/PUT candidate states.
- Added Intraday Research Scoreboard by symbol/horizon with mean/median returns, win rate, >=10% rate and TP10/SL10 first-touch statistics.
- Extended representative contracts to preserve bid/ask sizes and IV for quality checks.
- Built 2026-10-02 SPY intraday bootstrap from 60 immutable prospective snapshots; no hindsight-fill of unavailable context.
- Built VPS systemd services/timers for SPY collector, multi-asset intraday collector and post-close dataset/report pipeline.
- Added secure deployment bundle workflow excluding .env and .venv; generated code bundle and 2026-10-02 data seed bundle.
- VPS Tailscale port 22 reachable; deployment upload blocked only because encrypted Hetzner SSH key is not loaded in ssh-agent. No passphrase stored or requested.
