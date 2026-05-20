# Task 5 Cloudflare Radar Verification

## Summary

- overall_status: pass_with_warnings
- tested_at: 2026-05-20T07:09:41Z
- token_present: yes
- cloudflare_ingestion_status: success
- daily_build_status: success

## Checks

### Syntax

Commands:

```sh
python3 -m py_compile scripts/ingest_cloudflare_radar.py
python3 -m py_compile scripts/generate_normalized_events.py
python3 -m py_compile scripts/run_daily_world_pulse.py
```

Result:

- `scripts/ingest_cloudflare_radar.py`: pass
- `scripts/generate_normalized_events.py`: pass
- `scripts/run_daily_world_pulse.py`: pass

### Environment

Values were not printed.

- DATABASE_URL is set: yes
- DATABASE_URL host: aws-1-ap-northeast-1.pooler.supabase.com
- CLOUDFLARE_API_TOKEN is set: yes
- CLOUDFLARE_API_TOKEN length: 53

### Token-missing Behavior

Command:

```sh
CLOUDFLARE_API_TOKEN= .venv/bin/python scripts/ingest_cloudflare_radar.py --dataset outages
```

Result:

- exit code: 0
- output: `Cloudflare Radar ingestion skipped: CLOUDFLARE_API_TOKEN is not set`
- daily build implication: this skip behavior is compatible with non-critical ingestion.

### Cloudflare Radar Ingestion

Initial live API check returned HTTP 400 with this non-secret error summary:

```text
You must send either range or start & end dates
```

Implementation adjustment:

- Added `dateRange=7d` to the Cloudflare Radar outages request.
- Added `startDate` parsing support for Cloudflare records.

Command:

```sh
.venv/bin/python scripts/ingest_cloudflare_radar.py --dataset outages
```

Result:

```text
Cloudflare Radar ingestion completed: dataset=outages seen=1 inserted=1 skipped_duplicates=0 record_count=1 errors=0
```

Duplicate verification command:

```sh
.venv/bin/python scripts/ingest_cloudflare_radar.py --dataset outages
```

Result:

```text
Cloudflare Radar ingestion completed: dataset=outages seen=1 inserted=0 skipped_duplicates=1 record_count=1 errors=0
```

### Raw Observations and Lineage

Command:

```sh
psql "$DATABASE_URL" -P pager=off -c "SELECT s.name, COUNT(*) FROM raw_observations ro JOIN sources s ON s.id = ro.source_id GROUP BY s.name ORDER BY COUNT(*) DESC;"
```

Result:

```text
USGS Earthquake Hazards Program | 880
Wikipedia Pageviews             | 24
NOAA SWPC                       | 12
Open Notify                     | 10
Cloudflare Radar                | 1
```

Command:

```sh
psql "$DATABASE_URL" -P pager=off -c "SELECT COUNT(*) AS raw_observations_without_lineage FROM raw_observations ro LEFT JOIN source_lineage sl ON sl.raw_observation_id = ro.id WHERE sl.id IS NULL;"
```

Result:

```text
raw_observations_without_lineage = 0
```

### Normalized Events

Command:

```sh
.venv/bin/python scripts/generate_normalized_events.py --source all
```

Result:

```text
Normalized events generation: source=usgs seen=880 inserted=0 updated=880 skipped=0 errors=0
Normalized events generation: source=wikipedia seen=24 inserted=0 updated=24 skipped=0 errors=0
Normalized events generation: source=cloudflare seen=1 inserted=1 updated=0 skipped=0 errors=0
Normalized events generation completed: source=all seen=905 inserted=1 updated=904 skipped=0 errors=0
```

Category/event count query result:

```text
geophysical | earthquake                   | 880
attention   | wikipedia_attention_snapshot | 24
internet    | internet_outage_observation  | 1
```

Cloudflare anomaly score check:

```text
cloudflare_scored_events = 0
```

Interpretation:

- Cloudflare Radar normalized event exists with `category=internet`.
- `event_type=internet_outage_observation`.
- Cloudflare Radar `anomaly_score` remains `NULL`.
- Existing earthquake and Wikipedia normalized event generation still works.

### Daily Build

Command:

```sh
.venv/bin/python scripts/run_daily_world_pulse.py --skip-backfill --days 30 --date 2026-05-18
```

Result:

- Cloudflare Radar ingest step executed.
- Cloudflare Radar ingest status: success.
- Daily build reached `World Pulse daily build completed.`
- Summary included:

```text
target_date: 2026-05-18
display_json: public/display/latest.json
share_image_png: public/share/world-pulse-latest.png
share_image_jpg: public/share/world-pulse-latest.jpg
x_post_text: public/share/world-pulse-latest.txt
```

### Generated Outputs

Existence checks:

```text
public/display/latest.json ok
public/share/world-pulse-latest.png ok
public/share/world-pulse-latest.jpg ok
public/share/world-pulse-latest.txt ok
```

Generated X post text:

```text
World Pulse | Data date: 2026-05-18
Latest Weirdness Score: 20
This data date is in the 20th percentile of the last 30 observed days.
Top signal: M5.4 earthquake near West Chile Rise
Not a forecast, alert, or recommendation.
#WorldPulse
```

Safety-language check:

- No new Cloudflare Radar warning-style wording was found in the X post text.
- The only matched term was the existing safety sentence: `Not a forecast, alert, or recommendation.`

Generated display payload summary:

```text
display_date: 2026-05-18
score: 20
score_version: weirdness_v0_2
top_cards: 3
quiet_signal_available: False
```

### GitHub Actions Workflow

Checked `.github/workflows/daily-world-pulse.yml`.

- `DATABASE_URL: ${{ secrets.DATABASE_URL }}` present: yes
- `CLOUDFLARE_API_TOKEN: ${{ secrets.CLOUDFLARE_API_TOKEN }}` present: yes
- `public/share/world-pulse-latest.jpg` verify target present: yes
- `public/share/world-pulse-latest.jpg` commit target present: yes
- token value hardcoded: no

### Git Status

Command:

```sh
git status
```

Result summary:

Code changes:

- `.github/workflows/daily-world-pulse.yml`
- `scripts/generate_normalized_events.py`
- `scripts/run_daily_world_pulse.py`
- `scripts/ingest_cloudflare_radar.py` (new)

Documentation changes:

- `README.md`
- `docs/automation_operation.md`
- `docs/day2_ingestion_status.md`
- `docs/task5_cloudflare_radar_verification.md` (new)

Generated output changes:

- `public/display/latest.json`

No commit or push was performed.

## Warnings

- Local shell does not provide a `python` command, so verification used `.venv/bin/python` for commands that require installed dependencies.
- Initial Cloudflare live request failed with HTTP 400 because the API requires `dateRange` or start/end dates. The implementation was adjusted to send `dateRange=7d`, and ingestion then succeeded.
- Database and external API verification required network access outside the default sandbox.

## Human Review Needed

1. Confirm GitHub Secret `CLOUDFLARE_API_TOKEN` is set in the repository.
2. Confirm the next GitHub Actions Daily World Pulse run succeeds.
3. Confirm https://worldpulse.today/ renders normally after deployment.
4. Confirm https://worldpulse.today/share/world-pulse-latest.jpg is visible after deployment.
5. Review and commit the code, documentation, and generated output changes when ready.
