# O5 Drift-Neutral + O6 Research Decision Engine

## Drift-neutral contract policy
Historical unconditional SPY drift cannot by itself authorize CALL or PUT.

Contract-direction research uses a centered terminal-return distribution. A validated directional model may then reweight UP/DOWN probability around that neutral distribution.

Without validated direction, contract evaluation can remain diagnostic, but O6 must return NO_TRADE_DIRECTION.

## O6 research decisions
Possible outputs:
- NO_TRADE_ACTIVITY
- NO_TRADE_DIRECTION
- NO_TRADE_NO_CONTRACT
- NO_TRADE_LIQUIDITY
- NO_TRADE_EV
- NO_TRADE_STRESS
- RESEARCH_CALL_CANDIDATE
- RESEARCH_PUT_CANDIDATE

A research candidate requires:
1. Activity Gate pass.
2. Validated direction UP or DOWN with >=5pp incremental edge.
3. Real/synthetic contract available.
4. Liquidity gate pass.
5. Conservative EV > 0.
6. Aligned stress robustness.

O6 is a research gate only. It does not place orders and does not unlock live or paper trading.

## Prospective collector integration
Collector schema upgraded to o1.2.
When market is open it stores:
- Alpaca market clock
- contemporaneous SPY snapshot
- current SPY OPEN
- OPEN-causal features
- O3 raw/calibrated/conservative probability
- Activity Gate status
- direction status
- O6 research decision
- option-chain snapshot

Expiration filtering now uses Alpaca market date from the market clock, not the laptop local calendar.

Current direction layer is NOT SUPPORTED, so an activity pass still resolves to NO_TRADE_DIRECTION. This is intentional.
