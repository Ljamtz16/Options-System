# O0 — Project Foundation

Date: 2026-10-01
Status: IN PROGRESS

## Objective
Create an isolated, reproducible research foundation for SPY Options Intelligence without modifying the frozen SPY Run10A research.

## Frozen scope
- Underlying: SPY only.
- Initial instruments: long CALL and long PUT.
- Default decision: NO_TRADE.
- Naked short options: prohibited.
- Spreads/multi-leg: deferred.
- Live trading: disabled.
- Paper trading: disabled until O8.

## Architecture
Market state -> underlying outcome distribution -> event probabilities -> option P&L distribution -> expected value after costs -> liquidity/risk gate -> CALL / PUT / NO_TRADE.

## Causality contract
All decisions must use only information available at decision time. Future quotes, IV, Greeks, strikes, expirations and labels cannot leak into earlier decisions.

## Project layout
src/options_system: production/research package.
tests: causal and contract tests.
data/raw: immutable/raw inputs.
data/processed: derived datasets.
artifacts: experiment outputs.
config: frozen experiment configuration.
docs: protocols, decisions and results.
scripts: reproducible entry points.

## Environment
Python virtual environment: .venv
Dependency installation initiated with Python 3.12.
Initial required test dependency: pytest.

## Validation
Contract tests cover SPY-only scope, CALL/PUT scope, NO_TRADE default and execution locks.
Validation remains pending until the isolated environment finishes installing and tests pass.

## O0 validation result
Status: PASSED
Validated: 2026-10-01
Environment: Python 3.12.10 / pytest 9.1.1
Command: .venv\Scripts\python.exe -m pytest -q tests\test_o0_contract.py
Result: 4 passed in 0.28s.
O0 is frozen as the project foundation unless a documented decision explicitly changes its contract.
