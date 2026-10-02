# Intraday Decision Engine v1

## Purpose
Research-only decision layer for 15/30/60 minute option horizons.
It never places paper or live orders.

## Decision precedence
1. Unsupported horizon -> NO_TRADE_HORIZON
2. Market state not supported -> NO_TRADE_STATE
3. Direction not validated or edge < 5pp -> NO_TRADE_DIRECTION
4. Liquidity failure -> NO_TRADE_LIQUIDITY
5. Expected return <= 0 -> NO_TRADE_EV
6. Stress/robustness failure -> NO_TRADE_STRESS
7. Valid UP -> RESEARCH_CALL_CANDIDATE
8. Valid DOWN -> RESEARCH_PUT_CANDIDATE

## Liquidity Gate v1
Default research policy:
- bid >= 0.05
- ask <= 50.00
- relative spread <= 20%
- bid/ask size >= 1 when sizes exist
- |delta| between 0.20 and 0.80

The policy is deliberately simple and must be validated against prospective fills before use as an execution policy.
## Research Scoreboard
For each symbol and horizon it reports:
- sample count
- mean/median option return
- positive-return win rate
- >=10% outcome rate
- TP10/SL10 first-touch rates when available

Scoreboard output:
`artifacts/intraday/intraday_scoreboard_v1.json`

## Separation from swing
Swing O6 remains independent. Intraday candidates cannot authorize swing trades and swing activity cannot authorize intraday trades.

## Current status
Direction is not yet prospectively supported. Therefore a live Market State observation should still resolve to NO_TRADE_DIRECTION unless a separately validated intraday direction model exists.
