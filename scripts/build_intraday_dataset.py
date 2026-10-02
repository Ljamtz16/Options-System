from options_system.intraday_dataset_v2 import build_intraday_dataset_v2

n=build_intraday_dataset_v2(
    "data/raw/intraday",
    "data/processed/intraday/intraday_options_v2.csv")
print(f"BUILT_INTRADAY_V2 rows={n}")