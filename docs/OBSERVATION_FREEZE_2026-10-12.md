# Observation freeze — effective 2026-10-12

The next phase is an observation window, not a search for new rules. Scientific signal definitions and entry-control logic are frozen for at least 5 additional New York sessions and preferably 10. Execution defects may be repaired because they change broker fidelity, not the hypothesis definition.

PUT remains frozen even if short-run performance stays weak. H03 remains frozen even if its small sample continues to look strong. Jev remains an independent comparator; its own confidence threshold is managed in Jev Lab and does not alter Options-System hypotheses.

Every review must distinguish: activation/candidate evidence, Local Paper selection/execution, Alpaca entry fill, Alpaca completed round trip. Core metrics are realized P&L, marked/realized drawdown where available, entry fill rate, round-trip rate, entry/exit slippage, and session-to-session stability. Win rate is descriptive, not the primary objective.

`config/observation_freeze_v01.json` records hashes of scientific rule files. `scripts/build_execution_funnel_report.py` reports drift and builds `artifacts/intraday/EXECUTION_FUNNEL_V01.json`; it is part of the VPS post-close pipeline so the funnel is refreshed automatically after each session. A DRIFT status means the observation window is no longer directly comparable and must be reviewed before using new results.

Execution repairs introduced before the window: broker-position reconciliation, no new mirrored entry while a residual broker position exists, no new mirrored entry inside the final three minutes, a broker-only safety exit in the final three minutes, and unique retries after expired/canceled/rejected exit orders. These repairs intentionally do not rewrite Local Paper historical outcomes.
