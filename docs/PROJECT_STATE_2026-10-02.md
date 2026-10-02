# SPY Options Intelligence — Project State 2026-10-02

## Research objective
Estimate market state and event probabilities, then evaluate real option contracts after spread/liquidity/robustness. Default output is NO TRADE.

## Safety/research boundary
- Research only.
- No live trading.
- Paper trading remains locked until later validation.
- Long CALL / long PUT only in current scope.
- Swing and intraday decisions are separated.

## Swing branch
O2: OPEN-causal H3 path excursion target.
O3: calibrated probability engine for H3 activity.
Direction: NOT_SUPPORTED.
O5: drift-neutral contract intelligence.
O6: research decision gate.
Collector schema: o1.4 for future captures.

## Market State inputs
- SPY daily/open state
- premarket and OPEN+5
- QQQ/IWM cross-market
- Cboe delayed VIX
- sector breadth XLK/XLF/XLE/XLV/XLI
- SPY option chain, IV, Greeks, skew, volume
- option surface by DTE and 25d/50d delta
- within-day snapshot changes
## Intraday branch
Universe: SPY, QQQ, IWM, AAPL, NVDA, MSFT, AMZN, META, TSLA.
Horizons: 5/15/30/60 minutes and EOD; decision candidates currently limited to 15/30/60.
Chain scope: DTE 0–7, including 0DTE when available.
Outcomes include:
- terminal return
- MFE / MAE
- first touch ±0.25% and ±0.50%
- representative CALL/PUT path return
- best/worst option return and P&L
- TP10/TP20 before SL10/SL20 targets

## Intraday contract research
Representative contract: near 50-delta, shortest DTE available.
Conservative P&L uses entry ask and exit bid.
Contract Selector Lab can compare 25d/40d/50d/60d and DTE families.
Liquidity Gate v1 checks quote validity, spread, sizes, price bounds and delta.
Intraday Decision Engine emits only research candidate states after validated state/direction/EV/liquidity/stress.

## Data collection
Windows collectors currently exist locally.
VPS deployment files are prepared to move collection off the laptop.
Raw snapshots are immutable/content-addressed.
Outcome labels are added only after the horizon is complete.
No historical bid/ask or provider fields are fabricated.
## 2026-10-02 bootstrap evidence
60 SPY prospective snapshots from 15:00–19:55 UTC were converted into an intraday bootstrap.
Blind representative option entry was negative on average after quoted spread:
- 15m CALL -2.14%, PUT -1.62%
- 30m CALL -1.26%, PUT -4.74%
- 60m CALL -3.71%, PUT -7.26%
Large isolated positive windows existed, confirming the need for selective state/direction gating rather than continuous entry.
This one-day overlapping sample is pipeline evidence, not profitability evidence.

## VPS automation prepared
Systemd units:
- options-spy-collector
- options-intraday-collector
- options-postclose
Collectors run every 5 minutes and self-skip when Alpaca reports market closed.
Post-close pipeline runs at 23:30 UTC.
Deployment bundles exclude `.env` and `.venv`.

## Current blocker
The VPS is online and Tailscale port 22 is reachable. The local Hetzner SSH key is encrypted and not loaded in Windows ssh-agent, so unattended upload cannot authenticate yet.

## Next evidence milestones
1. Deploy to VPS after SSH key unlock.
2. Accumulate full-session multi-asset intraday snapshots.
3. Run quality audits and daily scoreboards.
4. Reach minimum labeled-day thresholds.
5. Run ablations/walk-forward direction research.
6. Only then consider paper-trading unlock criteria.
