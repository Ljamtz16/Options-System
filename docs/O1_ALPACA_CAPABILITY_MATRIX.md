# O1 — Alpaca Capability Matrix

Verified: 2026-10-01

| Data element | Official API | Account/plugin probe | O1 classification |
|---|---|---|---|
| Active SPY contracts | Yes | Verified | AVAILABLE |
| Inactive/expired SPY contracts | Yes | Verified on 2026-09-30 expiry | AVAILABLE |
| Current bid/ask | Yes | Verified previously | AVAILABLE |
| Current trades | Yes | Snapshot/chain supported | AVAILABLE |
| Current IV | Snapshot/chain | Supported | AVAILABLE, may be null |
| Current Greeks | Snapshot/chain | Supported | AVAILABLE, may be null |
| Historical option bars | Since Feb-2024 | REST endpoint not exposed by ChatGPT Alpaca connector | API AVAILABLE / ACCESS TEST PENDING |
| Historical option trades | Since Feb-2024 | REST endpoint not exposed by connector | API AVAILABLE / ACCESS TEST PENDING |
| Historical option quotes | No historical endpoint found in current official option reference | Latest only found | NOT CONFIRMED |
| Historical IV series | No dedicated historical endpoint verified | Not exposed | DERIVABLE from point-in-time prices if inputs exist |
| Historical Greeks series | No dedicated historical endpoint verified | Not exposed | DERIVABLE, not provider-history |
| Open interest | Contract metadata when available | Verified, nullable | AVAILABLE WITH MISSINGNESS |

## Important interpretation
Alpaca documents historical option data availability from February 2024.
Indicative is a derivative feed; its quotes are modified and trades delayed. OPRA is the consolidated options feed and requires subscription.
Current Greeks/IV are calculated values and may be absent when required inputs are invalid or unavailable.

## Architecture consequence
Never backfill historical Greeks from today's snapshot.
Persist provider-native historical prices/trades first. Reconstructed IV/Greeks, if used, must be explicitly labeled derived and computed only from contemporaneously available inputs.
