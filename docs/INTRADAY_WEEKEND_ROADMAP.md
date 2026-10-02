# Intraday Weekend Roadmap — Integrated

## Official integrated branch
The project now has two research branches sharing Market State:
- Swing: H1/H3.
- Intraday: 5m/15m/30m/60m/EOD.

## Intraday universe
SPY, QQQ, IWM, AAPL, NVDA, MSFT, AMZN, META, TSLA.

## Outcomes v2
For each checkpoint and symbol the dataset can record:
- terminal return
- MFE / MAE
- first touch ±25 bp and ±50 bp
- CALL/PUT best, worst and terminal return
- conservative P&L using entry ask / exit bid
- TP-before-SL labels at 10% and 20%

## Contract research grid
Research selector supports 25d/40d/50d/60d and DTE buckets 0, 1, 2-3, 4-7 days.
No contract family is authorized for trading yet.

## Ablation order
Baseline → Premarket → OPEN5 → VIX → Cross-market → Sectors → Options.
A block is retained only if it adds stable validation value later.

## Automation
The live intraday collector remains scheduled every 5 minutes while the market is open.
The post-session task rebuilds dataset v2 and daily report automatically.

## Research boundary
Paper/live execution stays disabled. Intraday outputs are observational until validation and O6-style gates are added.