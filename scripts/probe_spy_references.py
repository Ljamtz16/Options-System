from options_system.underlying_history import causal_spot_reference
for d in ("2026-09-28","2026-09-29","2026-09-30"):
    r=causal_spot_reference("SPY",d+"T13:30:00Z",d+"T20:00:00Z")
    print(d,r["price"],r["observed_at_utc"],r["feed"])
