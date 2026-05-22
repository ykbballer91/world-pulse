# Event-Page Persistence Candidate Dry Run

## Purpose

Classify Phase 2.4 event-page candidates before any database storage work.

This file is a dry run. It does not create tables, run migrations, or write event-page links to the database.

## Input Scope

- Dates: 2026-05-20, 2026-05-14, 2026-05-15
- Events: 9 earthquake events
- Candidate links: 47

## Classification Rules

- `store_by_default`: registry reviewed, exists=true, confidence high or medium.
- `hold_for_review`: registry provisional or registry low-confidence candidate.
- `exclude`: exists=false or heuristic fallback candidate unless later promoted.

## Summary

- Total candidate links: 47
- Store by default: 36
- Hold for review: 3
- Exclude: 8

## Counts by Date

| Date | Total | Store by default | Hold for review | Exclude |
| --- | ---: | ---: | ---: | ---: |
| 2026-05-14 | 15 | 11 | 0 | 4 |
| 2026-05-15 | 15 | 12 | 2 | 1 |
| 2026-05-20 | 17 | 13 | 1 | 3 |

## Store by Default Examples

| Date | Event | Page | Group | Confidence | Source | Review status | Exists | Reason category | Classification |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-05-20 | M6.6 earthquake near southern East Pacific Rise | `Earthquake` | core | high | registry | reviewed | true | exists | store_by_default |
| 2026-05-20 | M6.6 earthquake near southern East Pacific Rise | `Seismology` | core | high | registry | reviewed | true | exists | store_by_default |
| 2026-05-20 | M6.6 earthquake near southern East Pacific Rise | `Seismic_wave` | core | high | registry | reviewed | true | exists | store_by_default |
| 2026-05-20 | M6.6 earthquake near southern East Pacific Rise | `East_Pacific_Rise` | context | high | registry | reviewed | true | exists | store_by_default |
| 2026-05-20 | M6.6 earthquake near southern East Pacific Rise | `Pacific_Ocean` | context | medium | registry | reviewed | true | exists | store_by_default |
| 2026-05-20 | M5.9 earthquake near 10 km NNW of China, Japan | `Earthquake` | core | high | registry | reviewed | true | exists | store_by_default |
| 2026-05-20 | M5.9 earthquake near 10 km NNW of China, Japan | `Seismology` | core | high | registry | reviewed | true | exists | store_by_default |
| 2026-05-20 | M5.9 earthquake near 10 km NNW of China, Japan | `Seismic_wave` | core | high | registry | reviewed | true | exists | store_by_default |
| 2026-05-20 | M5.9 earthquake near 10 km NNW of China, Japan | `Japan` | context | medium | registry | reviewed | true | exists | store_by_default |
| 2026-05-20 | M5.9 earthquake near 8 km E of Wadomari, Japan | `Earthquake` | core | high | registry | reviewed | true | exists | store_by_default |
| 2026-05-20 | M5.9 earthquake near 8 km E of Wadomari, Japan | `Seismology` | core | high | registry | reviewed | true | exists | store_by_default |
| 2026-05-20 | M5.9 earthquake near 8 km E of Wadomari, Japan | `Seismic_wave` | core | high | registry | reviewed | true | exists | store_by_default |

## Hold for Review Examples

| Date | Event | Page | Group | Confidence | Source | Review status | Exists | Reason category | Classification |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-05-20 | M6.6 earthquake near southern East Pacific Rise | `Tsunami` | core | medium | registry | provisional | true | exists | hold_for_review |
| 2026-05-15 | M6.7 earthquake near 49 km ESE of Ōfunato, Japan | `Ōfunato` | context | low | registry | reviewed | true | ambiguous_location | hold_for_review |
| 2026-05-15 | M6.7 earthquake near 49 km ESE of Ōfunato, Japan | `Tōhoku_region` | context | low | registry | reviewed | true | ambiguous_location | hold_for_review |

## Exclude Examples

| Date | Event | Page | Group | Confidence | Source | Review status | Exists | Reason category | Classification |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-05-20 | M6.6 earthquake near southern East Pacific Rise | `Mid-ocean_ridge` | context | medium | heuristic | unreviewed | true | exists | exclude |
| 2026-05-20 | M5.9 earthquake near 10 km NNW of China, Japan | `China` | context | medium | heuristic | unreviewed | true | exists | exclude |
| 2026-05-20 | M5.9 earthquake near 8 km E of Wadomari, Japan | `Wadomari` | context | low | heuristic | unreviewed | true | ambiguous_location | exclude |
| 2026-05-14 | M6.2 earthquake near 271 km WSW of Tual, Indonesia | `Tual` | context | low | heuristic | unreviewed | true | ambiguous_location | exclude |
| 2026-05-14 | M5.3 earthquake near 32 km WNW of Darien, Colombia | `Colombia` | context | medium | heuristic | unreviewed | true | exists | exclude |
| 2026-05-14 | M5.3 earthquake near 32 km WNW of Darien, Colombia | `Darien` | context | low | heuristic | unreviewed | true | ambiguous_location | exclude |
| 2026-05-14 | M5.2 earthquake near Volcano Islands, Japan region | `Volcano_Islands` | context | low | heuristic | unreviewed | true | ambiguous_location | exclude |
| 2026-05-15 | M5.4 earthquake near 119 km SSE of Lorengau, Papua New Guinea | `Lorengau` | context | low | heuristic | unreviewed | true | ambiguous_location | exclude |

## Notes

- All `exists=false` candidates would be excluded. This run has zero `exists=false` rows after cleanup.
- Heuristic fallback candidates can remain useful in dry-run review, but should not be persisted by default.
- Low-confidence registry candidates need a review step before storage.
- Pageview-window measurements should be stored only for persisted event-page links.
