# O2 OPEN-Causal Magnitude Engine v0.2

Decision anchor: OPEN(t). Feature as-of: completed session t-1, except current open used only for open_t/gap. Outcomes are labels and may use future path.

Features: 17 causal OPEN features. Same-day close/high/low/volume mutation and future mutation invariance tests pass.

Outcomes:
- H1=t, H3=t..t+2, H5=t..t+4, H10=t..t+9.
- terminal return = close(label_end)/open_t - 1.
- MFE=max(high/open_t-1); MAE=min(low/open_t-1).
- label_end is inclusive horizon end.

Legacy O2/O3/O4 predictive artifacts are preserved but marked SUPERSEDED_DIAGNOSTIC_ONLY in artifacts/PRE_OPEN_CAUSALITY_MANIFEST.json.

Dataset v0.2: 1,472 decisions, 2020-10-20 through 2026-08-31.

## Target sweep
Old-style terminal H3 |return|>=1% is NOT SUPPORTED after causal correction: Validation delta Brier -0.01018; delta LogLoss -0.26803.

Path excursion candidates are stronger. H1 +/-1% looked strong in aggregate but failed 2023 stability, so it is not promoted.

H3 path excursion +/-1% means max(MFE,-MAE)>=1% at any time in t..t+2. Aggregate Validation: delta Brier +0.05456; delta LogLoss +0.18377.
Year stability:
- 2022: +0.08776 Brier, +0.28410 LogLoss
- 2023: +0.02124 Brier, +0.08305 LogLoss
Already-inspected diagnostics:
- 2024: -0.00239 / -0.01329
- 2025: +0.02441 / +0.05575
- 2026 through Aug: +0.01146 / +0.04130

## Frozen research candidate
O2_OPEN_PATH_1PCT_H3_V02_CANDIDATE
Target: P(max(MFE_H3,-MAE_H3)>=1% | OPEN-causal state).
Status: RESEARCH_CANDIDATE, not production-supported and not pristine OOS-confirmed.
Direction: none. This target predicts excursion magnitude/activity only.
O6 remains locked.
