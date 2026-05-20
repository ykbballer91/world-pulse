# World Pulse Day 2 Ingestion Status

This document records the current successful Day 2 ingestion state.

## Principles

- 予測しない
- 煽らない
- 投資判断・医療判断・政治判断に使わせない

## Completed Ingestion Sources

### USGS Earthquake

- Scope: global earthquakes, M4.0 and above
- `raw_observations` save: successful
- `source_lineage` save: successful

Run example:

```sh
python scripts/ingest_usgs_earthquakes.py --hours 24 --min-magnitude 4
```

### NOAA SWPC

- Scope: Kp index
- Scope: X-ray flux
- Storage granularity: one `raw_observations` row per API response
- `raw_observations` save: successful
- `source_lineage` save: successful

Run examples:

```sh
python scripts/ingest_noaa_swpc.py --dataset kp
python scripts/ingest_noaa_swpc.py --dataset xray
python scripts/ingest_noaa_swpc.py --dataset all
```

### Open Notify

- Scope: ISS current position
- Scope: people currently in space
- Storage granularity: one `raw_observations` row per API response
- `raw_observations` save: successful
- `source_lineage` save: successful

Run examples:

```sh
python scripts/ingest_open_notify.py --dataset iss
python scripts/ingest_open_notify.py --dataset astros
python scripts/ingest_open_notify.py --dataset all
```

### Wikipedia Pageviews

- Scope: `en.wikipedia` top pageviews
- Default date: two days ago in UTC
- Daily aggregation delay mitigation: implemented
- Duplicate prevention: same `source_id`, `dataset`, `project`, `access`, and `date` is not saved twice
- `raw_observations` save: successful
- `source_lineage` save: successful

Run examples:

```sh
python scripts/ingest_wikipedia_pageviews.py
python scripts/ingest_wikipedia_pageviews.py --date 2026-05-19
python scripts/ingest_wikipedia_pageviews.py --project en.wikipedia --access all-access --date 2026-05-19
```

### Cloudflare Radar

- Scope: optional public Internet outage/anomaly observations
- Storage granularity: one `raw_observations` row per API response
- Requires: `CLOUDFLARE_API_TOKEN`
- Daily build behavior: non-critical; skipped when token is absent

Run example:

```sh
python scripts/ingest_cloudflare_radar.py --dataset outages
```

## Current DB Verification Result

Source counts:

```text
USGS Earthquake Hazards Program | 20
NOAA SWPC                       | 2
Open Notify                     | 2
Wikipedia Pageviews             | 1
```

Source lineage coverage:

```text
raw_observations_without_lineage = 0
```

## Day 2 Verification Commands

Install dependencies:

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run SQL migration:

```sh
psql "$DATABASE_URL" -f sql/001_init.sql
psql "$DATABASE_URL" -f sql/002_create_baseline_distributions.sql
psql "$DATABASE_URL" -f sql/003_create_normalized_events.sql
psql "$DATABASE_URL" -f sql/004_create_score_versions_and_weirdness_scores.sql
psql "$DATABASE_URL" -f sql/005_create_display_log.sql
psql "$DATABASE_URL" -f sql/006_add_quiet_signal_to_display_log.sql
psql "$DATABASE_URL" -f sql/007_add_layer_to_sources.sql
```

Run ingestion scripts:

```sh
python scripts/ingest_usgs_earthquakes.py --hours 24 --min-magnitude 4
python scripts/ingest_noaa_swpc.py --dataset all
python scripts/ingest_open_notify.py --dataset all
python scripts/ingest_wikipedia_pageviews.py
python scripts/ingest_cloudflare_radar.py --dataset outages
```

Verify counts by source:

```sh
psql "$DATABASE_URL" -c "SELECT s.name, COUNT(*) FROM raw_observations ro JOIN sources s ON s.id = ro.source_id GROUP BY s.name ORDER BY s.name;"
```

Verify source lineage coverage:

```sh
psql "$DATABASE_URL" -c "SELECT COUNT(*) AS raw_observations_without_lineage FROM raw_observations ro LEFT JOIN source_lineage sl ON sl.raw_observation_id = ro.id WHERE sl.id IS NULL;"
```

Verify internal source layers:

```sh
psql "$DATABASE_URL" -c "SELECT name, source_type, layer FROM sources ORDER BY name;"
psql "$DATABASE_URL" -c "SELECT name FROM sources WHERE layer IS NULL;"
```

Source layers are internal only. World Pulse classifies sources into `reality`, `attention`, and `context` for future Reality-Attention Gap analysis. The public UI remains Signal Position, and gap scores are not exposed publicly. The current stored `attention` layer is provisional: Wikipedia Pageviews is treated as delayed reflection / interpretation proxy, not immediate attention. An immediate attention layer is not implemented yet.

Run Python syntax checks:

```sh
python3 -m py_compile scripts/ingest_usgs_earthquakes.py
python3 -m py_compile scripts/ingest_noaa_swpc.py
python3 -m py_compile scripts/ingest_open_notify.py
python3 -m py_compile scripts/ingest_wikipedia_pageviews.py
python3 -m py_compile scripts/ingest_cloudflare_radar.py
```

## Remaining Day 2 API

- No additional Day 2 API is required for the beta ingestion set.

## Notes

Day 2 ingestion stores raw observations and source lineage only. It does not generate alerts, forecasts, risk judgments, advice, ranking interpretations, or LLM summaries.
