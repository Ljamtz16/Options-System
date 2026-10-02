from options_system.prospective_dataset import build_dataset
n=build_dataset("data/raw/prospective","data/processed/prospective/prospective_market_state_v1.csv")
print(f"BUILT rows={n}")
