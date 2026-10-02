from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"

UNDERLYING = "SPY"
ALLOWED_OPTION_SIDES = ("call", "put")
DEFAULT_DECISION = "NO_TRADE"
LIVE_TRADING_ENABLED = False
PAPER_TRADING_ENABLED = False
