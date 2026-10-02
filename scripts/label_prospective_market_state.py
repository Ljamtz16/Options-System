from options_system.prospective_outcome_labeler import label_dataset
n=label_dataset("data/processed/prospective/prospective_market_state_v1.csv","data/processed/prospective/prospective_market_state_labeled_v1.csv")
print(f"LABELED rows={n}")
