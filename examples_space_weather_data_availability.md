# Space Weather Data Availability

## Purpose

Audit stored NOAA SWPC data before Space Weather dry-run analysis.

Requested lookback: 90 days

## Stored Data

| Dataset | Raw rows | Records | Earliest raw observed_at | Latest raw observed_at | Earliest record time | Latest record time | Usable days | Coverage note |
| --- | ---: | ---: | --- | --- | --- | --- | ---: | --- |
| kp | 19 | 6805 | 2026-05-20 00:33 UTC | 2026-05-22 04:42 UTC | 2026-05-19 18:35 UTC | 2026-05-22 04:42 UTC | 2.42 | provider current window only |
| xray | 19 | 382882 | 2026-05-20 00:33 UTC | 2026-05-22 04:42 UTC | 2026-05-13 00:36 UTC | 2026-05-22 04:42 UTC | 9.17 | provider current window only |

## Summary

Stored NOAA SWPC data does not currently provide a full 90-day historical record. The dry-run uses the available provider current windows only.
