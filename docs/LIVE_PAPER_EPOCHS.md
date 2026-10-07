# LIVE_PAPER epochs

The 2026-10-07 epoch starts with $1,000 of new virtual capital, zero P&L and a new ledger. The previous state and capital-allocation control are archived in `artifacts/intraday/paper_epochs/before_LIVE_P1_2026-10-07`. Original immutable captures and hypothesis definitions remain unchanged. This action does not call a broker.

`scripts/start_live_paper_epoch.py --epoch-id LIVE_P1_2026-10-07 --cash 1000` is idempotent: invoking it again with the same ID keeps all subsequent trades. A reset is refused if there are open or unresolved positions. The exact prior state bytes, control bytes and their SHA-256 hashes are retained before the new state is atomically installed.

The new state retains all seen signal IDs, marks earlier tracker signals as processed and advances the snapshot cursor to the reset time. The live runner additionally rejects snapshots and signals at or before the epoch start. Its shared state lock and atomic write prevent a concurrent runner from restoring an older balance. The current 40% premium budget is retained, with a maximum of one contract per trade. P2 experimental entry controls remain disabled.

Research observation plan: technical check after 5 market sessions, interim review after 10, main review after 30 (roughly six market weeks), and robustness follow-up at 60–90. Also require at least 100 independent completed trades per hypothesis before drawing an initial performance conclusion; overlapping minute snapshots do not count as independent trades. A day with no trade is informative about coverage, but does not add a profit label. These are project review targets, not guarantees of statistical sufficiency or profitability.

Jev confidence diagnostics currently require 20 training days plus 5 later holdout days, and at least 100 training plus 25 heldout nonoverlapping resolved labels under the same frozen model/execution configuration. This only permits a candidate for review. For reliable isotonic calibration, aim for substantially more labeled opportunities (around 1,000 as a general guideline), retain later out-of-sample validation, and account for day-level dependence. The 75% Jev threshold remains unchanged.

Calibration reference: scikit-learn, Probability calibration, https://scikit-learn.org/stable/modules/calibration.html (isotonic regression is more prone to overfitting on small datasets; independent calibration/validation data are needed).
