# Dashboard session views: Today vs Historical

## Decision

The intraday dashboard is session-scoped. Its default view is **Today**, defined by the `America/New_York` market date. Historical data is opened explicitly with `?mode=history&day=YYYY-MM-DD`.

The browser must never download every historical session just to display the current day. The server must also avoid rebuilding immutable closed sessions during every intraday refresh.

## Why this architecture exists

The original dashboard embedded accumulated multi-day data and metadata in large JavaScript artifacts. As the number of sessions and symbols grew, every refresh carried an increasing cost in browser memory, transfer size, JSON parsing, and server-side rebuild work. A visual date filter alone would not solve that problem because the historical payload would still be loaded before filtering.

The new design makes the selected market session the unit of loading and caching. This keeps resource use bounded by one session instead of by the age of the project.

## Runtime layout

`artifacts/intraday/sessions/` contains generated runtime views and is intentionally ignored by Git:

- `index.json`: lightweight manifest with available dates, row counts, symbols and latest capture.
- `YYYY-MM-DD.json`: market rows for one session only.
- `YYYY-MM-DD.meta.json`: metadata scoped to one session while preserving current account balances.
- `analysis.json`: accumulated/post-close research analysis; requested only in Historical mode.
- `views-cache.json`: local build cache; never published to the web root.

The tracked `dashboard_loader.js` reads `index.json`, selects exactly one date and then fetches only that date's data and metadata.

## Today mode

Today mode is optimized for active-session monitoring:

1. Determine today's date in `America/New_York`, not in the browser's local timezone.
2. Load `sessions/index.json`.
3. Load only `sessions/<today>.json` and `sessions/<today>.meta.json`.
4. Do not load `analysis.json`.
5. Poll only the small index every 60 seconds; reload when its generation marker changes.
6. Hide accumulated research/replay views that are not required for the active session.

The live publisher sets `OPTIONS_BUILD_SCOPE=today`. Historical/counterfactual reports are reused from the latest post-close build instead of being recomputed every few minutes.

## Historical mode

Historical mode is explicit and read-oriented:

1. The index lists prepared sessions without opening their full JSON files.
2. Selecting a date navigates to that date, replacing the current session in memory rather than accumulating sessions.
3. `analysis.json` is loaded only here because cumulative evidence is relevant to research review.
4. Paper Trading risk controls are disabled in Historical mode. Inspecting an old date must not mutate current trading configuration.
5. Historical session metadata is cached. Closed sessions are not rewritten on each live refresh; post-close may refresh them when needed.

Current broker/account balances can still be shown because they represent current account state. Day-specific ledgers, episodes and execution records are scoped to the selected date so they are not confused with current balances.

## Server-side bounded work

Intraday raw captures are indexed by lightweight headers. Full option-chain payloads are loaded on demand and only one payload is retained by the shared snapshot cache at a time.

Processed intraday data is stored by market session under `data/processed/intraday/sessions/`. A session is rebuilt only when its source fingerprint or transformation algorithm changes. The compatibility aggregate CSV can then be assembled from prepared daily CSV files without reparsing every raw option-chain capture.

The dashboard data builder likewise keeps closed session JSON files and regenerates only changed/missing sessions plus the current day.

## Publication and Nginx permissions

Source artifacts may remain private to the application user. Web copies under `/var/www/options-dashboard` must be readable by Nginx (`www-data`).

`tempfile.mkstemp()` creates temporary files with mode `0600`. When those files were atomically renamed into the web root, Nginx returned `403 Forbidden` for `sessions/*.json` even though the dashboard HTML itself returned `200`.

`publish_web()` therefore:

- copies to a temporary file in the destination directory;
- explicitly sets the **published copy** to `0644`;
- atomically renames it into place;
- repairs an existing unchanged web copy if its mode is not `0644`;
- leaves the source artifact permissions unchanged.

This is tested as a regression case by forcing a published file to `0600` and requiring the next publish to restore `0644`.

## Failure isolation

The dashboard manifest is published after its dependencies so the browser should not observe a new index pointing at session files that have not yet been copied. Writes use temporary files plus atomic replacement to avoid serving partially-written JSON.

If the requested session is not prepared yet, the UI shows an empty/not-ready state rather than falling back silently to another date.

## Non-goals

This change does not delete historical raw captures, alter frozen hypotheses, merge Jev and Options accounts, or change broker order behavior. It changes how prepared research/dashboard data is built, published and loaded.

## Validation

Core regression coverage is in `tests/test_session_cache.py` and verifies:

- snapshot headers are reused without reparsing unchanged raw captures;
- only changed sessions rebuild;
- Today dashboard output contains only today's session;
- closed session archives remain incremental;
- metadata is scoped to the selected session;
- lazy snapshot access matches the prior eager paper-replay result;
- published session JSON is `0644`, including repair of an existing `0600` copy.

Operational HTTP checks should return `200` for:

```text
/
/dashboard_loader.js
/sessions/index.json
/sessions/<today>.json
/sessions/<today>.meta.json
/sessions/analysis.json
```

The last endpoint is intentionally fetched by the browser only in Historical mode.
