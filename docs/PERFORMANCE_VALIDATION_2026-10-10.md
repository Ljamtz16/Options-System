# Runtime performance validation — 2026-10-10

Validation after session-scoped dashboard, Alpaca reconciliation/retry, execution funnel and Jev 65% observation-freeze changes.

## VPS headroom

- RAM: 7.6 GiB total; about 6.6 GiB available after stabilization.
- Disk: 75 GiB volume, about 53 GiB free (27% used).
- Stable load average after Jev optimization: 0.13 / 0.48 / 0.59.
- CPU and memory PSI during the stable sample: 0.00.
- No recent Nginx errors.

## Options live services

Observed systemd memory usage remained small: Alpaca mirror about 11 MiB current / 26 MiB peak, fast paper tracker about 14 MiB, and paper control about 10 MiB. Nginx serves the current 3.2 MB session JSON locally in about 10 ms; the 986-byte session index is sub-millisecond. Today mode polls only the index, not the large session payload.

## Postclose

The 2026-10-09 postclose completed successfully from 22:30:06 to 22:34:05 UTC (3m59s) with about 234.7 CPU-seconds, approximately one CPU core on average and outside market hours. The new execution-funnel report itself costs only about 0.13 s and 51 MiB peak RSS.

`vps_postclose.py` now runs at lower OS priority (`OPTIONS_POSTCLOSE_NICE`, default 10) and applies a per-task timeout (`OPTIONS_POSTCLOSE_TASK_TIMEOUT_SECONDS`, default 1200 s) so a regression cannot run indefinitely.

## Jev issue found and fixed

Before optimization, Jev comparator repeatedly loaded all 8,509 decisions and historical quote paths every 20 seconds, averaging about 46% CPU and 478 MiB RSS. The worker also revisited history every 10 seconds and averaged about 15% CPU.

Jev now persists consumed snapshots, pending comparison IDs and the last processed decision rowid. Only new or still-open work is revisited. Normal measured runs are about 0.10 s / 26 MiB for the worker and 0.11 s / 28 MiB for the comparator; stable CPU was about 0.2–0.3% each.

The VPS user services for the Jev worker and comparator additionally enforce `CPUQuota=50%`, `MemoryMax=384M`, `Nice=10` and `OOMScoreAdjust=500`, protecting the broker executor and the rest of the VPS from a research-process regression.

## Storage runway

Full recent sessions add roughly 1.2–1.4 GiB/day combined across intraday and prospective raw snapshots. With about 53 GiB free, the planned additional 5–10 observation sessions fit comfortably. Review/offload should happen before extending retention materially beyond the planned window.

## Operational thresholds

Investigate before continuing unattended operation if available RAM falls below 2 GiB, disk usage exceeds 70%, sustained load approaches the vCPU count, Jev worker/comparator hit their cgroup limits repeatedly, or the postclose runtime materially exceeds its current ~4-minute baseline.
