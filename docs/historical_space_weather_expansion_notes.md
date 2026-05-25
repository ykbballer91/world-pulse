# Historical Space Weather Expansion Notes

## Purpose

Track the Phase 3.2 expansion from three historical Space Weather samples to a small source-recorded set with cached pageview retrieval.

## Retrieval Policy

The audit script now uses a local pageview cache, retry attempts, and a polite request delay. This keeps repeated dry-runs from requesting the same Wikimedia window again when a successful response is already stored locally.

## Cache Policy

- Default cache directory: `.cache/wiki_pageviews`
- Cache keys use page title, start date, and end date.
- Successful responses are cached.
- Local cache files are not intended for repository storage.

## Expanded Event Set

The initial expansion uses six source-recorded events. This is below the long-term target of ten, but keeps the first cached dry-run small enough to review manually.

## Review Notes

- May 2024 remains the strongest known sample from the earlier run.
- Older solar flare samples are useful for method testing, but source context should remain attached to each example.
- Pageview movement is daily aggregated reference-system activity only.
- No DB writes are part of this phase.

## Next Step

If the six-event set remains stable, expand to ten source-recorded events before preparing an internal AI/RAG technical note.
