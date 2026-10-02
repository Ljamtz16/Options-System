# Intraday Options Engine v1

## Scope
Research-only intraday options branch sharing the broader Market State architecture.
It does not replace the swing H1/H3 engine.

## Universe
SPY, QQQ, IWM, AAPL, NVDA, MSFT, AMZN, META, TSLA.

## Capture cadence
Every 5 minutes while Alpaca market clock is open.
The scheduler runs continuously; the collector itself rejects closed-market runs.

## Option window
DTE 0-7, including 0DTE when available.
Strike window: +/-3% around contemporaneous spot.
Snapshot schema: intraday_o1.1.
## Outcomes
For each snapshot/symbol the dataset targets:
- underlying return and UP/DOWN at 5, 15, 30 and 60 minutes
- end-of-day return
- representative CALL/PUT selected near 50 delta
- conservative option P&L using entry at ask and exit at bid

## Global context
Each capture also stores:
- VIX delayed context from Cboe
- SPY/QQQ/IWM cross-market state
- sector breadth from XLK, XLF, XLE, XLV and XLI

## Boundary
No paper/live orders are enabled.
The output is a prospective research dataset for later validation of CALL/PUT/NO TRADE intraday decisions.
