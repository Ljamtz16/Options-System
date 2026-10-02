from options_system.intraday_scoreboard import build_scoreboard

r=build_scoreboard(
    "data/processed/intraday/intraday_options_v2.csv",
    "artifacts/intraday/intraday_scoreboard_v1.json",
)
print(f"SCOREBOARD symbols={len(r)}")
