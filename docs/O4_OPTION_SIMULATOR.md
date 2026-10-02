# O4 Option Simulator

## Scope v0.1
Translate SPY scenarios into theoretical long CALL/PUT values and P&L. O4 does not select a trade.

Inputs include option type, strike, DTE, entry premium, IV, multiplier, risk-free rate, elapsed time, SPY scenario, IV shift and explicit costs.

## Core invariants
- expiry value equals intrinsic value;
- CALL value/P&L responds positively to upside relative to downside;
- PUT value/P&L responds positively to downside relative to upside;
- costs reduce net P&L exactly;
- simulator matches the existing Black-Scholes engine interface;
- O2/O3 magnitude probability is direction-neutral and cannot be silently interpreted as bullish or bearish.

## Magnitude-event bridge
For p_move = P(|SPY move| >= threshold), the initial neutral bridge allocates p_move equally between up/down only as a scenario convention, not as a learned directional probability. Remaining probability is assigned to the flat/non-event scenario.

O4 carries EV under p_raw, p_calibrated and p_conservative separately. No trade decision is permitted from O4 alone.

## Known limitations
Current v0.1 is Black-Scholes scenario repricing, not an empirical options return model. It still needs SPY dividend treatment, point-in-time rates, IV-path scenarios, bid/ask/slippage model, empirical move-size distribution beyond the 1% threshold, and validation against historical option observations.

## Empirical H3 distribution bridge v0.2

O4 now supports empirical H3 return distributions and weighted repricing instead of relying only on artificial +1%/-1%/flat scenarios.

A standardized 18-feature nearest-neighbor diagnostic (k=100, scaler fit on Train only) was evaluated OOS:
- Train episodes: 304
- OOS episodes: 665
- neighbor conditional mean-return MAE: 0.0112845
- global Train mean-return MAE: 0.0113886

The improvement is small. Therefore nearest-neighbor frequency is NOT promoted as a replacement for O3 probability estimation.

Architecture decision:
- O3 estimates P(|H3 return| >= 1%);
- historical development episodes provide the empirical return shape conditional on EVENT (|return|>=1%) and NON_EVENT (|return|<1%);
- O4 mixes those empirical samples using p_raw / p_calibrated / p_conservative and reprices the option under every weighted scenario;
- directional proportions inside each historical conditional distribution are empirical descriptors, not a new directional ML claim.

This separates event probability from move-size distribution and avoids treating every event as exactly +/-1%.

Future hardening: use only causally permissible development samples for prospective decisions; add MFE/MAE/high-low path scenarios, IV response distributions, dividends/rates, and bid/ask execution.

## Path, IV and execution hardening v0.3

### H3 path
O4 now has path metrics anchored to the decision/open price: terminal return, MFE from daily highs and MAE from daily lows. Barrier order is only asserted when daily OHLC supports it. If upper and lower barriers are both touched in the same daily candle, label is AMBIGUOUS_SAME_SESSION.

### IV
Historical provider-native IV is unavailable in the tested Alpaca historical API. O4 therefore does not invent historical IV. It supports explicit IV stress scenarios (default research grid: -3 vol points, unchanged, +3 vol points). IV response must remain scenario/stress analysis until a defensible historical IV reconstruction or prospective snapshot history exists.

### Execution
Historical bid/ask is likewise unavailable from the tested historical endpoint. Prospective snapshots do provide quotes. Execution model for long options uses bid/ask, configurable fraction-of-spread slippage and explicit fees. Invalid/zero quotes are rejected, not repaired.

### Stress cube
O4 can evaluate empirical return samples across elapsed-time and IV-shift grids. This exposes theta/IV sensitivity rather than hiding it inside one expected P&L.

Research rule: an EV result based on theoretical mids without executable quotes is theoretical, not executable performance.
