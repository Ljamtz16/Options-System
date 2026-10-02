# O1 — Canonical Data Contract (draft)

## Contract identity
provider, feed, underlying_symbol, option_symbol, option_type, strike, expiration, multiplier.

## Observation identity
observed_at_utc, retrieved_at_utc, source_endpoint, request_id_or_snapshot_id.

## Market fields
underlying_price, bid, ask, bid_size, ask_size, last_trade, last_trade_size, volume, open_interest.

## Derived fields
mid = (bid + ask) / 2 when both are valid.
spread = ask - bid.
spread_pct = spread / mid when mid > 0.
dte_seconds and dte_days are derived from observation timestamp and expiration convention.
moneyness is derived from strike and contemporaneous underlying price.

## Volatility/Greeks
provider_iv and provider Greeks are stored only when actually returned at that timestamp.
derived_iv / derived_delta / derived_gamma / derived_theta / derived_vega must use separate columns and provenance.

## Missingness
Missing provider values remain null. No forward fill or retrospective substitution is allowed in raw data.
