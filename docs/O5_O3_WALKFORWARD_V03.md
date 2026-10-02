# O3 -> O5 Integrated Walk-Forward 2024-2026 v0.3

Status: DIAGNOSTIC ONLY. The 2024-2026 period has already been inspected and is not pristine OOS.

The frozen O3 OPEN probability model and Platt calibration are used without refitting. Each session uses only OPEN-causal features. Historical scenario windows contain only H3 outcomes completed before the decision date.

Research gates:
1. conservative path-excursion probability >= 0.80
2. synthetic contract conservative EV > 0
3. EV remains > 0 under IV shocks -3/0/+3 vol points at the same H3 elapsed-day horizon

Results across 666 sessions:
- Activity Gate passes: 145 (21.77%)
- Among gate passes, path excursion >=1% actually occurred: 93.10%
- Sessions with at least one robust synthetic contract: 35 (5.26% of all sessions; 24.14% of gated sessions)
- Positive-EV synthetic contracts across gated sessions: 139
- Robust synthetic contracts: 63
- Best robust contract type: CALL 35, PUT 0
- Mean best synthetic EV across robust sessions: +$28.03/contract

Previous diagnostic walk-forward had 219 positive-best-EV sessions, all CALL. The integrated causal activity pipeline reduces that to 35 robust sessions, but does NOT remove CALL concentration.

By year:
- 2024: gate 23/252; robust sessions 15; CALL 15 / PUT 0
- 2025: gate 93/250; robust sessions 15; CALL 15 / PUT 0
- 2026 through Aug: gate 29/164; robust sessions 5; CALL 5 / PUT 0

Terminal-return bias:
- all 666 sessions: mean H3 +0.1733%, P(up)=59.01%
- activity-gated 145 sessions: mean +0.4601%, P(up)=63.45%
- robust-contract 35 sessions: mean +0.6119%, P(up)=65.71%

Interpretation:
The magnitude/activity gate is not a directional model, but the historical conditional terminal-return distribution used by O5 is more bullish among selected high-activity states. This creates CALL preference. It must NOT be described as learned directional edge.

Therefore direction_guard remains mandatory. No CALL/PUT authorization is permitted until a separately validated directional layer adds incremental information beyond the conditional directional baseline. O6 remains locked.

All contract results are synthetic: fixed IV assumptions, synthetic spreads and Black-Scholes repricing. They are research diagnostics, not historical realized option returns.
