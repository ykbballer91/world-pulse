# World Pulse

World Pulse stores raw public observations with source lineage for transparent, non-advisory analysis.

## Principles

- no prediction
- no fear amplification
- no trading/investment/medical/political advice

## Included Scope

This repository currently includes USGS earthquake ingestion, NOAA SWPC solar activity ingestion, Open Notify ingestion, Wikipedia Pageviews ingestion, and optional Cloudflare Radar ingestion. It does not include login, payment, alerts, forecasting, market data, political data, health advice, or SNS raw content.

## Setup

Install dependencies:

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run the SQL migration:

```sh
psql "$DATABASE_URL" -f sql/001_init.sql
psql "$DATABASE_URL" -f sql/002_create_baseline_distributions.sql
psql "$DATABASE_URL" -f sql/003_create_normalized_events.sql
psql "$DATABASE_URL" -f sql/004_create_score_versions_and_weirdness_scores.sql
psql "$DATABASE_URL" -f sql/005_create_display_log.sql
psql "$DATABASE_URL" -f sql/006_add_quiet_signal_to_display_log.sql
psql "$DATABASE_URL" -f sql/007_add_layer_to_sources.sql
```

Run USGS ingestion for the last 24 hours:

```sh
python scripts/ingest_usgs_earthquakes.py --hours 24 --min-magnitude 4
```

Run NOAA SWPC ingestion for Kp index and X-ray flux:

```sh
python scripts/ingest_noaa_swpc.py --dataset kp
python scripts/ingest_noaa_swpc.py --dataset xray
python scripts/ingest_noaa_swpc.py --dataset all
```

Run Open Notify ingestion for ISS position and people in space:

```sh
python scripts/ingest_open_notify.py --dataset iss
python scripts/ingest_open_notify.py --dataset astros
python scripts/ingest_open_notify.py --dataset all
```

Run Cloudflare Radar ingestion for public Internet outage/anomaly observations:

Cloudflare Radar is optional and requires `CLOUDFLARE_API_TOKEN`. It is ingested as raw observations with source lineage, normalized with `category=internet`, and treated as non-critical in the daily build. Initial `anomaly_score` values may be `NULL` until a stable baseline exists.

```sh
python scripts/ingest_cloudflare_radar.py --dataset outages
python scripts/ingest_cloudflare_radar.py --dataset outages --database-url "$DATABASE_URL"
```

Source layers:

World Pulse internally classifies sources into `reality`, `attention`, and `context` layers. These layers are internal only. The public UI remains Signal Position, and gap scores are not exposed publicly.
Internal layer positions and layer gaps are stored for research and validation. Layer gaps are not forecasts, alerts, warnings, or recommendations.
Wikipedia `Main_Page` is also excluded from topic-level attention inspection where available. The original attention layer values are preserved, while additional internal `excluding_main_page` fields are stored for validation.
Topic-level attention also excludes non-topic Wikipedia namespace pages such as `Special:`, `Wikipedia:`, `Help:`, `File:`, and `Category:`. Additional internal `topic_pages` fields are stored for validation.
Internal attention validation is split into `global_topic` and `targeted` streams. `targeted` only checks whether predefined category-related pages appear in stored Wikipedia top pages; it is not exposed publicly.

Export internal layer difference examples:

```sh
python scripts/export_gap_examples.py --days 30 --database-url "$DATABASE_URL" --output examples.md
```

Run Wikipedia Pageviews ingestion for daily top articles:

Wikipedia top pageviews は日次集計の反映遅れがあるため、デフォルトではUTCで2日前の日付を取得します。
同一日付・同一project・同一accessのWikipedia top pageviewsは重複保存しません。

```sh
python scripts/ingest_wikipedia_pageviews.py
python scripts/ingest_wikipedia_pageviews.py --date 2026-05-19
python scripts/ingest_wikipedia_pageviews.py --project en.wikipedia --access all-access --date 2026-05-19
```

Run Day 2 backfill helpers:

```sh
python scripts/backfill_day2_sources.py --source usgs --days 7
python scripts/backfill_day2_sources.py --source wikipedia --days 7
python scripts/backfill_day2_sources.py --source all --days 7
python scripts/backfill_day2_sources.py --source all --days 30
python scripts/backfill_day2_sources.py --source all --days 30 --database-url "$DATABASE_URL"
```

Calculate initial Day 3 baseline distributions:

Baseline distributions save `stddev_value` for normalized event `anomaly_score` calculation.

```sh
python scripts/calculate_baseline_distributions.py --source usgs --days 7
python scripts/calculate_baseline_distributions.py --source wikipedia --days 7
python scripts/calculate_baseline_distributions.py --source all --days 7
```

Generate Day 4 normalized events:

```sh
python scripts/generate_normalized_events.py --source usgs
python scripts/generate_normalized_events.py --source wikipedia
python scripts/generate_normalized_events.py --source all
```

Calculate the internal Signal Position score:

Score versions:

- `weirdness_v0_1`: raw positive anomaly weighted score.
- `weirdness_v0_2`: percentile rank of the daily raw score within the recent baseline window.
- Public UI label: Signal Position.
- Internal score version: `weirdness_v0_2`.
- The public label avoids presenting the value as a risk, alert, or danger score.
- Current public display uses Signal Position backed by `weirdness_v0_2`.

Daily aggregation events such as `wikipedia_attention_snapshot` may contribute to scoring context. They are excluded from the displayed Top signal to keep the UI focused on individual observed signals.

Quiet Signal is an optional display-only field. It highlights one individual observed signal above the recent baseline within the current data window. It is not a forecast, alert, warning, or recommendation. It may be absent on many data dates.

```sh
python scripts/calculate_weirdness_score.py
python scripts/calculate_weirdness_score.py --date 2026-05-18
```

Generate one-day display payload:

Display `top_cards` may include both `score_contributor` and `context_only` signals.
The beta page and share outputs label the value as Signal Position and show the data date, because Wikipedia top pageviews can lag daily availability.

```sh
python scripts/generate_display_payload.py
python scripts/generate_display_payload.py --date 2026-05-17
```

Export display payload JSON:

```sh
python scripts/export_display_payload_json.py
python scripts/export_display_payload_json.py --date 2026-05-17
```

Generate share images:

The share image generator outputs both PNG and JPG files:

- `public/share/world-pulse-latest.png`
- `public/share/world-pulse-latest.jpg`
- `public/share/world-pulse-YYYY-MM-DD.png`
- `public/share/world-pulse-YYYY-MM-DD.jpg`

```sh
python scripts/generate_share_image.py
python scripts/generate_share_image.py --date 2026-05-17
```

Generate X post text:

```sh
python scripts/generate_x_post_text.py
python scripts/generate_x_post_text.py --date 2026-05-17
```

Run the daily World Pulse build:

World Pulse beta uses a 30-day baseline for initial operation. Wikipedia sample counts may be lower than 30 when daily top pageviews are not yet available for every date in the lookback window.
Wikipedia 30-day backfill is intended for initial setup and manual correction. The daily build keeps the 30-day baseline calculation, but uses a short, non-critical Wikipedia backfill window to reduce API rate-limit pressure. If Wikimedia returns `429 Too Many Requests`, existing data is used and the daily build continues with a warning.

```sh
python scripts/run_daily_world_pulse.py
python scripts/run_daily_world_pulse.py --days 30
python scripts/run_daily_world_pulse.py --date 2026-05-17
python scripts/run_daily_world_pulse.py --skip-ingest --skip-backfill --date 2026-05-17
```

Run the local beta page:

```sh
python3 -m http.server 8080 -d public
```

Open `http://localhost:8080/`.

`public/about.html` explains methodology, data window, sources, and safety principles. It is static and deployed by Cloudflare Pages with the rest of `public/`.

Automation operation:

```text
docs/automation_operation.md
```

GitHub Actions requires `DATABASE_URL`. `CLOUDFLARE_API_TOKEN` can also be set as a repository secret for Cloudflare Radar ingestion, but it is optional initially.

Verify raw observation and source lineage counts:

```sh
psql "$DATABASE_URL" -c "SELECT (SELECT COUNT(*) FROM raw_observations) AS raw_observations_count, (SELECT COUNT(*) FROM source_lineage) AS source_lineage_count;"
psql "$DATABASE_URL" -c "SELECT COUNT(*) AS raw_observations_without_lineage FROM raw_observations ro LEFT JOIN source_lineage sl ON sl.raw_observation_id = ro.id WHERE sl.id IS NULL;"
```
