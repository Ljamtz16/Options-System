# SPY Intraday State Analysis — 2026-10-02

## Scope
Exploratory analysis of 60 real prospective SPY snapshots captured on 2026-10-02.
This is one session only and is hypothesis generation, not statistical validation.

## Baseline observation
Unfiltered long CALL/PUT entries using ask-in / bid-out were negative on average at 15/30/60 minutes, despite isolated large winners.
This confirms that selection/gating matters more than simply having option exposure.

## Strongest preliminary CALL pattern
At 60 minutes, the exploratory rule:
- ATM IV increasing vs prior snapshot
- put/call IV skew decreasing vs prior snapshot
- put/call volume ratio increasing vs prior snapshot

selected 9 windows.
Observed mean CALL return: +2.10%.
CALL +10% frequency: 44.4%.
CALL loss <= -10% frequency: 22.2%.

This pattern is named CALL_FLOW_REVERSAL for research only.
It is not authorized as a trading rule.
## Preliminary PUT pattern
A simple static put/call-volume rule was not enough.
The cleaner exploratory PUT condition was:
- put/call IV skew > 0.0045
- put/call near-ATM volume ratio < 1.05

At 15 minutes this selected 22 windows:
- mean PUT return: +3.08%
- +10% frequency: 18.2%
- <= -10% frequency: 13.6%

At 30 minutes it was roughly flat (+0.17% mean), and at 60 minutes it was negative.
This suggests any PUT effect may be short-horizon and should not be generalized.

## Cross-market observation
The strongest CALL windows often occurred while SPY, QQQ and IWM were already below their session opens.
That is more consistent with rebound/mean-reversion behavior than straightforward momentum.

For 60-minute CALL winners >= +10% with cross-market fields available:
- SPY was about -0.24% from open on average
- QQQ about -0.37%
- IWM about -0.36%

Therefore the first research hypothesis should test market-state reversal rather than assume that bullish options require a bullish contemporaneous tape.

## Features that cannot be evaluated from this one day
Premarket return/range and OPEN+5 values are constant across the day's snapshots, so they cannot explain within-day differences on a single session.
Their value requires multiple prospective days.

## Research conclusion
Do not promote any rule from this analysis.
Carry forward two hypotheses only:
1. CALL_FLOW_REVERSAL — dynamic IV/skew/put-call-volume changes may identify 60-minute rebound CALL windows.
2. SHORT_HORIZON_PUT_SKEW — relatively high put IV skew with non-elevated near-ATM put/call volume may identify some 15-minute PUT windows.

Both require prospective multi-day confirmation and comparison against unconditional baselines.