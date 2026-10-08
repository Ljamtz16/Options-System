# Options-System Alpaca Paper Mirror

Purpose: mirror only NEW Options-System LIVE_PAPER decisions into a dedicated Alpaca Paper account while preserving the local account as the research source of truth.

## Safety invariants

- Trading endpoint is hardcoded to `https://paper-api.alpaca.markets`.
- Disabled unless `OPTIONS_ALPACA_PAPER_ENABLED=true`.
- Order submission disabled unless `OPTIONS_ALPACA_SUBMIT_ORDERS=true`.
- `OPTIONS_ALPACA_MIRROR_START_UTC` is mandatory; older trades are never backfilled.
- A local trade first observed after it is already CLOSED becomes `SKIPPED_MISSED_LIVE_ENTRY`.
- One contract is mirrored because the local LIVE_PAPER currently uses one contract per entry.
- Jev credentials are not reused.

## Broker account balance

Keep the Alpaca Paper account at >= $25,000 (the standard paper balance is normally larger) to avoid paper PDT checks becoming an artificial execution constraint. Options-System continues to enforce a $1,000 shadow capital/risk model independently.

## Secret file on VPS

Create `~/.config/options-system/options-alpaca-paper.env` with mode 600:

```text
OPTIONS_ALPACA_PAPER_ENABLED=false
OPTIONS_ALPACA_SUBMIT_ORDERS=false
OPTIONS_ALPACA_API_KEY_ID=<dedicated paper key>
OPTIONS_ALPACA_API_SECRET_KEY=<dedicated paper secret>
OPTIONS_ALPACA_MIRROR_START_UTC=<future activation timestamp>
OPTIONS_ALPACA_SHADOW_CAPITAL=1000
```

Never commit this file.

## Validation sequence

1. `python3 scripts/run_options_alpaca_mirror.py --check-account`
2. Set `OPTIONS_ALPACA_PAPER_ENABLED=true` but keep `OPTIONS_ALPACA_SUBMIT_ORDERS=false`.
3. Run the mirror and inspect planned `ACTION` lines. No orders are submitted.
4. Set a future `OPTIONS_ALPACA_MIRROR_START_UTC` for the next session.
5. Only after validation, set `OPTIONS_ALPACA_SUBMIT_ORDERS=true`.
6. Run the mirror immediately after every local LIVE_PAPER update.

## Execution semantics

Entry: market `buy_to_open` of the exact contract selected by local LIVE_PAPER.
Exit: market `sell_to_close` when the local trade closes for TP10, SL10, HORIZON, or SESSION_CLOSE.

The mirror records local ASK/BID references and Alpaca fills separately so entry/exit slippage and P&L divergence can be audited.
