# NOAA Snapshot Accumulation Plan

## Purpose

Explain how World Pulse accumulates NOAA SWPC current-window observations over time so that Space Weather Reality-Reflection dry-runs can be rerun after 30, 60, and 90 days.

## Current Finding

The Phase 3 Space Weather dry-run found that the stored NOAA SWPC range is short:

- Kp currently has about 2.42 usable days.
- X-ray currently has about 9.17 usable days.
- Current NOAA ingestion is not a true historical replay.
- Space Weather dry-runs should remain provisional until more daily snapshots accumulate.

## Why Accumulation Is Needed

NOAA provider current windows are useful, but they are not enough for historical validation. World Pulse needs repeated daily captures to build its own observation history. Space Weather evaluation should be rerun after enough stored snapshots exist to compare event candidates across a broader period.

## Accumulation Milestones

### Day 0

- Treat current Space Weather output as provisional dry-run evidence only.
- Do not use it as a primary commercial sample category.

### After 30 Days

- Rerun the Space Weather dry-run.
- Check whether Kp >= 5 appears in stored snapshots.
- Check whether more X-ray M-class candidates appear.
- Compare pageview movement against the candidate reference pages.

### After 60 Days

- Evaluate whether Space Weather has clearer Reflection movement than earthquake.
- Assess whether reference-data freshness examples are improving.
- Review whether the candidate registry remains clean without broad heuristic expansion.

### After 90 Days

- Decide whether Space Weather becomes a primary commercial sample category.
- Decide whether to build database persistence for Space Weather event-page links.
- Compare Space Weather samples with earthquake and internet categories if available.

## Daily Ingestion Expectations

- Daily World Pulse should continue ingesting NOAA Kp and X-ray data.
- Each day's current-window fetch contributes to local historical coverage.
- Deduplication should preserve unique payloads.
- `source_lineage` should remain complete.
- Long-range validation should stay manual and outside the scheduled daily workflow.

## Validation Queries

These are example queries to adapt if actual column names differ.

### NOAA Source Coverage

```sql
SELECT
  s.name,
  MIN(ro.observed_at) AS earliest_observed_at,
  MAX(ro.observed_at) AS latest_observed_at,
  COUNT(*) AS raw_rows,
  COUNT(DISTINCT ro.observed_at::date) AS observed_days
FROM raw_observations ro
JOIN sources s ON ro.source_id = s.id
WHERE s.name ILIKE '%NOAA%'
GROUP BY s.name
ORDER BY s.name;
```

### Source Lineage Check

```sql
SELECT COUNT(*) AS raw_without_lineage
FROM raw_observations ro
LEFT JOIN source_lineage sl ON ro.ingestion_run_id = sl.ingestion_run_id
WHERE sl.ingestion_run_id IS NULL;
```

### Normalized Event Coverage If Available

```sql
SELECT
  source_name,
  event_type,
  MIN(event_time) AS earliest_event_time,
  MAX(event_time) AS latest_event_time,
  COUNT(*) AS events
FROM normalized_events
WHERE source_name ILIKE '%NOAA%'
GROUP BY source_name, event_type
ORDER BY source_name, event_type;
```

## Rerun Commands

### 30-Day Review

```bash
python3 scripts/dry_run_space_weather_reflection.py \
  --days 30 \
  --kp-threshold 5 \
  --xray-threshold M \
  --database-url "$DATABASE_URL" \
  --output examples_space_weather_entity_linking_dryrun_30d.md
```

### 60-Day Review

```bash
python3 scripts/dry_run_space_weather_reflection.py \
  --days 60 \
  --kp-threshold 5 \
  --xray-threshold M \
  --database-url "$DATABASE_URL" \
  --output examples_space_weather_entity_linking_dryrun_60d.md
```

### 90-Day Review

```bash
python3 scripts/dry_run_space_weather_reflection.py \
  --days 90 \
  --kp-threshold 5 \
  --xray-threshold M \
  --database-url "$DATABASE_URL" \
  --output examples_space_weather_entity_linking_dryrun_90d.md
```

## What Not To Claim

Do not claim:

- real-time public awareness
- causality
- service relevance
- infrastructure effect
- emergency relevance
- prediction
- market relevance

## Decision Rule

Continue Space Weather if:

- enough events accumulate
- candidate pages remain clean
- pageview-window movement becomes more interpretable
- examples become stronger than earthquake samples

Pause Space Weather if:

- Kp/X-ray candidates remain sparse
- pageview movement remains weak
- Wikipedia is not a useful Reflection proxy for this category

## Next Review Dates

Use relative milestones from the accumulation start date:

- 30 days after accumulation start
- 60 days after accumulation start
- 90 days after accumulation start
