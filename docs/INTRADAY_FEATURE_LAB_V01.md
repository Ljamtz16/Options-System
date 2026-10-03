# Intraday Feature Lab v0.1

## Status
EXPLORATORY ONLY. The current sample is 60 snapshots from 2026-10-02, one trading session.
Nothing in this lab changes or validates frozen hypotheses H01/H02.

## Dataset
`data/processed/intraday/intraday_feature_lab_v01.csv` joins contemporaneous Market State,
the representative 0-7 DTE ~50-delta CALL/PUT available at each snapshot, contract liquidity,
and future outcomes that are used only as labels.

Added contract features include delta, DTE, bid/ask, relative spread, quote sizes and IV.
Time context includes UTC time and minutes from the regular US open.

## Event labels
For CALL and PUT at 15/30/60 minutes:
- MFE >= +10%;
- TP +10% before SL -10%.

The outcome columns and labels are targets, never eligible predictor features.

## Baselines on 2026-10-02
CALL MFE>=10%: 22.0% / 28.8% / 33.9% at 15/30/60m.
PUT MFE>=10%: 20.3% / 27.1% / 30.5%.
CALL TP10-before-SL10: 16.9% / 22.0% / 23.7%.
PUT TP10-before-SL10: 20.3% / 27.1% / 27.1%.

## Univariate discovery protocol
Candidate thresholds use within-sample quartiles with minimum support of 8 observations.
Ranking by lift is for hypothesis generation only. Absolute price thresholds (for example SPY
price levels) are session-specific context and must not be promoted as general rules.
Future returns, MFE, MAE, labels and frozen-hypothesis activation fields are excluded from predictors.

A candidate H03/H04 may be written only as a new EXPLORATORY specification. It does not enter
the prospective scoreboard until separately frozen under a new version before observing its validation data.


## Multivariate candidate discovery
The lab also evaluates conjunctions of two or three contemporaneous rules. Absolute price
levels are excluded from general candidates. A combination requires at least 8 observations
and at least 3 observations in each half of the discovery session. Temporal support requires
a non-zero target-event rate in both halves.

### H03 candidate
`H03_CALL_RELATIVE_WEAKNESS_REVERSAL_CANDIDATE`:
- IWM from open <= -0.3338%;
- SPY from open <= -0.2141%;
- target: CALL TP +10% before SL -10% within 60 minutes.

Discovery-only result: 9 observations, 77.8% target rate versus 23.7% unconditional baseline.
The first/second-half rates were 100% and 66.7%. This is not validation because both halves
belong to the same session and overlapping 5-minute observations are correlated.

No H04 PUT candidate is promoted at this stage: the strongest PUT combinations had zero target
events in the second half of the discovery session.

H03 remains `NOT_FROZEN` and is not connected to the prospective tracker.

## Auditoría de censura y episodios — 2026-10-03

Se corrigió el tratamiento de horizontes incompletos cerca del cierre. Un camino parcial ya no puede demostrar un resultado negativo por ausencia de evento. Un TP_FIRST o SL_FIRST ya observado conserva validez; MFE >= +10% ya observado también conserva el positivo. NEITHER y MFE < +10% requieren cobertura completa del horizonte.

Después de la corrección, CALL TP10-before-SL10 a 60m pasa de 59 observaciones aparentes a 50 observables. Los 14 positivos no cambian, por lo que el baseline descriptivo de la sesión cambia de 23.73% a 28.00%.

La regla H03 original NO fue reajustada:
- IWM from open <= -0.003338055604745982
- SPY from open <= -0.002140966419266088

Sigue produciendo 9 activaciones y 7/9 TP-first entre esas activaciones. Para reducir pseudo-replicación, las activaciones se agrupan en episodios cuando la separación entre activaciones consecutivas es <= 6 minutos. Esto produce 6 episodios. Usando exclusivamente la primera activación como entrada del episodio, 5/6 tuvieron TP +10% antes que SL -10% en la sesión diagnóstica del 2026-10-02.

Este 5/6 (83.3%) NO es una estimación prospectiva ni una expectativa de rentabilidad: procede de un único día usado para descubrimiento. H03 permanece EXPLORATORY_ONLY / NOT_FROZEN.

También se corrigió minutes_from_us_open para calcular 09:30 America/New_York de forma timezone-aware y se excluyeron explícitamente outputs de modelos/decisiones previas del escáner de predictores.
