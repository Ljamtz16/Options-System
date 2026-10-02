# Options Intelligence

Research system for probabilistic options decisions with strict causal and audit rules.

## Branches
### Swing / SPY
- SPY only.
- H1/H3 research horizons.
- Long CALL and long PUT only.
- O2/O3/O5/O6 architecture.

### Intraday / multi-asset
- SPY, QQQ, IWM, AAPL, NVDA, MSFT, AMZN, META, TSLA.
- 5/15/30/60 minute and EOD outcomes.
- 0–7 DTE option research, including 0DTE when available.
- Long CALL / long PUT only.

## Default decision
NO TRADE.
Paper and live trading remain locked.

## Pipeline
Market State -> event/direction probabilities -> contract selection -> conservative P&L/EV -> liquidity/stress gates -> research CALL / PUT / NO TRADE.

## Research rules
- Point-in-time data only.
- No future labels or quotes may enter earlier decisions.
- No fabricated provider fields.
- Entry/exit option research defaults to ask-in / bid-out.
- New feature blocks must prove incremental value before promotion.
- Run10A remains external/frozen.

## Documentation entry points
- `docs/PROJECT_STATE_2026-10-02.md`
- `docs/INTRADAY_OPTIONS_ENGINE_V1.md`
- `docs/INTRADAY_DECISION_ENGINE_V1.md`
- `docs/VPS_DEPLOYMENT_AND_AUTOMATION.md`
- `docs/TODAY_SPY_BOOTSTRAP_2026-10-02.md`

## Reproduce on VPS
```bash
git clone https://github.com/Ljamtz16/Options-System.git /home/ljamtz/options-system
cd /home/ljamtz/options-system
cp .env.example .env
# Edit .env locally on the VPS and add Alpaca credentials.
bash deploy/scripts/install_vps.sh
```

The repository includes the frozen research artifacts required by the runtime and a curated compressed prospective-data seed from 2026-10-02. Expanded raw/processed datasets are intentionally ignored to keep Git history manageable.

Never commit `.env`, SSH keys, API secrets, runtime logs, or local virtual environments.
