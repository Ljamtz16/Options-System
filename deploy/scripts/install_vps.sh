#!/usr/bin/env bash
set -euo pipefail
ROOT=/home/ljamtz/options-system
cd "$ROOT"

if [ ! -f .env ]; then
  echo "ERROR: $ROOT/.env missing" >&2
  echo "Copy .env.example to .env and add Alpaca credentials locally." >&2
  exit 2
fi

python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
if [ -f requirements-dev.txt ]; then
  .venv/bin/pip install -r requirements-dev.txt
fi

SEED=artifacts/options-system-data-seed-2026-10-02.tar.gz
if [ -f "$SEED" ]; then
  tar -xzf "$SEED" -C "$ROOT"
  echo "Prospective seed restored from $SEED"
fi
sudo cp deploy/systemd/options-*.service /etc/systemd/system/
sudo cp deploy/systemd/options-*.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now options-intraday-collector.timer
sudo systemctl enable --now options-spy-collector.timer
sudo systemctl enable --now options-postclose.timer

.venv/bin/python -m pytest tests/test_o6_research_engine.py tests/test_intraday_decision_liquidity_scoreboard.py -q

echo "Install complete. Verify timers with: systemctl list-timers 'options-*'"
