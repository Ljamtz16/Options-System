import csv,json
from pathlib import Path
from options_system.market_state_readiness import market_state_training_readiness
p=Path("data/processed/prospective/prospective_market_state_labeled_v1.csv")
rows=list(csv.DictReader(open(p,encoding="utf-8"))) if p.exists() else []
x=market_state_training_readiness(rows)
Path("artifacts/market_state").mkdir(parents=True,exist_ok=True)
Path("artifacts/market_state/MARKET_STATE_V1_READINESS.json").write_text(json.dumps(x,indent=2),encoding="utf-8")
print(json.dumps(x))
