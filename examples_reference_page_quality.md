# Reference Page Candidate Quality Review

Generated at: 2026-05-22T00:24:06Z

## Purpose

Review candidate reference-page quality before any database storage design.

## Cleanup Rules Applied

- Directional modifiers are removed when they break known feature titles.
- Generated `_region` titles are avoided unless explicitly known.
- Distance and direction fragments are trimmed before location parsing.
- Low-confidence town candidates are kept only when explicitly allowed in this dry run.

## Candidate Quality Rows

| Candidate page title | Source event | Exists | Reason category | Suggested replacement |
| --- | --- | --- | --- | --- |
| Earthquake | M6.6 earthquake near southern East Pacific Rise | true | exists | none |
| Seismology | M6.6 earthquake near southern East Pacific Rise | true | exists | none |
| Seismic_wave | M6.6 earthquake near southern East Pacific Rise | true | exists | none |
| Tsunami | M6.6 earthquake near southern East Pacific Rise | true | exists | none |
| East_Pacific_Rise | M6.6 earthquake near southern East Pacific Rise | true | exists | none |
| Pacific_Ocean | M6.6 earthquake near southern East Pacific Rise | true | exists | none |
| Mid-ocean_ridge | M6.6 earthquake near southern East Pacific Rise | true | exists | none |
| Earthquake | M5.9 earthquake near 10 km NNW of China, Japan | true | exists | none |
| Seismology | M5.9 earthquake near 10 km NNW of China, Japan | true | exists | none |
| Seismic_wave | M5.9 earthquake near 10 km NNW of China, Japan | true | exists | none |
| Japan | M5.9 earthquake near 10 km NNW of China, Japan | true | exists | none |
| China | M5.9 earthquake near 10 km NNW of China, Japan | true | exists | none |
| Earthquake | M5.9 earthquake near 8 km E of Wadomari, Japan | true | exists | none |
| Seismology | M5.9 earthquake near 8 km E of Wadomari, Japan | true | exists | none |
| Seismic_wave | M5.9 earthquake near 8 km E of Wadomari, Japan | true | exists | none |
| Japan | M5.9 earthquake near 8 km E of Wadomari, Japan | true | exists | none |
| Wadomari | M5.9 earthquake near 8 km E of Wadomari, Japan | true | ambiguous_location | none |
| Earthquake | M6.2 earthquake near 271 km WSW of Tual, Indonesia | true | exists | none |
| Seismology | M6.2 earthquake near 271 km WSW of Tual, Indonesia | true | exists | none |
| Seismic_wave | M6.2 earthquake near 271 km WSW of Tual, Indonesia | true | exists | none |
| Indonesia | M6.2 earthquake near 271 km WSW of Tual, Indonesia | true | exists | none |
| Tual | M6.2 earthquake near 271 km WSW of Tual, Indonesia | true | ambiguous_location | none |
| Earthquake | M5.3 earthquake near 32 km WNW of Darien, Colombia | true | exists | none |
| Seismology | M5.3 earthquake near 32 km WNW of Darien, Colombia | true | exists | none |
| Seismic_wave | M5.3 earthquake near 32 km WNW of Darien, Colombia | true | exists | none |
| Colombia | M5.3 earthquake near 32 km WNW of Darien, Colombia | true | exists | none |
| Darien | M5.3 earthquake near 32 km WNW of Darien, Colombia | true | ambiguous_location | none |
| Earthquake | M5.2 earthquake near Volcano Islands, Japan region | true | exists | none |
| Seismology | M5.2 earthquake near Volcano Islands, Japan region | true | exists | none |
| Seismic_wave | M5.2 earthquake near Volcano Islands, Japan region | true | exists | none |
| Japan | M5.2 earthquake near Volcano Islands, Japan region | true | exists | none |
| Volcano_Islands | M5.2 earthquake near Volcano Islands, Japan region | true | ambiguous_location | none |
| Earthquake | M6.7 earthquake near 49 km ESE of Ōfunato, Japan | true | exists | none |
| Seismology | M6.7 earthquake near 49 km ESE of Ōfunato, Japan | true | exists | none |
| Seismic_wave | M6.7 earthquake near 49 km ESE of Ōfunato, Japan | true | exists | none |
| Japan | M6.7 earthquake near 49 km ESE of Ōfunato, Japan | true | exists | none |
| Ōfunato | M6.7 earthquake near 49 km ESE of Ōfunato, Japan | true | ambiguous_location | none |
| Tōhoku_region | M6.7 earthquake near 49 km ESE of Ōfunato, Japan | true | ambiguous_location | none |
| Earthquake | M5.4 earthquake near 119 km SSE of Lorengau, Papua New Guinea | true | exists | none |
| Seismology | M5.4 earthquake near 119 km SSE of Lorengau, Papua New Guinea | true | exists | none |
| Seismic_wave | M5.4 earthquake near 119 km SSE of Lorengau, Papua New Guinea | true | exists | none |
| Papua_New_Guinea | M5.4 earthquake near 119 km SSE of Lorengau, Papua New Guinea | true | exists | none |
| Lorengau | M5.4 earthquake near 119 km SSE of Lorengau, Papua New Guinea | true | ambiguous_location | none |
| Earthquake | M4.9 earthquake near 11 km WNW of Palca, Peru | true | exists | none |
| Seismology | M4.9 earthquake near 11 km WNW of Palca, Peru | true | exists | none |
| Seismic_wave | M4.9 earthquake near 11 km WNW of Palca, Peru | true | exists | none |
| Peru | M4.9 earthquake near 11 km WNW of Palca, Peru | true | exists | none |

## Summary

- Candidate rows reviewed: 47
- `exists=false` rows after cleanup: 0
- Remaining low-confidence rows should be manually reviewed before database storage.
