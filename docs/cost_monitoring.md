# Cost Monitoring

## Purpose

Track the services and resources that World Pulse depends on, and identify when costs become a constraint before that constraint affects daily build continuity.

This document is for internal review. It does not change scripts, database schema, public display, or GitHub Actions.

---

## Current Cost Areas

### Supabase

- Free tier: provides a PostgreSQL database sufficient for the current data volume.
- Usage components: database row count, storage, egress, and compute hours.
- Current status: within free tier as of Phase 3 dry-run.

### GitHub Actions

- Free tier: provides a monthly minute budget for public repositories.
- Usage: the daily scheduled workflow runs approximately once per day. Duration establishes the per-day minute consumption.
- Current status: within free tier. Exact per-run duration should be established after two weeks of stable builds.

### Domain

- `worldpulse.today` is a paid annual registration.
- Renewal date should be tracked separately and renewed well in advance.

### X API (if live posting is enabled)

- Current status: dry-run only. No X API calls are made.
- Posting via the X API may require a paid tier depending on post frequency and media upload.
- Cost must be confirmed in the X Developer Portal before enabling live posting.
- See `x_auto_posting_plan.md` for the full pre-live checklist.

### LLM or External Processing APIs

- Current status: none in use. The daily build does not use any LLM or third-party processing API.
- If LLM processing is considered in a future phase, it should be reviewed separately and treated as a new cost area.

---

## Monthly Review

Review the following items once per month:

| Item | What to Check |
|------|---------------|
| GitHub Actions minutes | Total minutes consumed in the billing cycle. Compare against the free tier monthly budget. |
| Supabase storage | Total rows and storage size. Confirm still within free tier limits. |
| Supabase database usage | Compute hours or query count if visible in the Supabase dashboard. |
| X API usage | Check only if live posting is enabled. Otherwise skip. |
| External API costs | Any services that bill per-call (e.g., Wikimedia bulk, USGS). Currently these are free public APIs. |

---

## Cost Review Triggers

The following conditions should prompt an unscheduled cost review, independent of the monthly schedule:

- **GitHub Actions minutes grow materially.** If build duration increases by more than 50% of the established baseline for more than seven consecutive days, identify the cause before costs grow further.
- **Supabase free tier approaches its row or storage limit.** If storage growth is consistently upward, evaluate whether old raw observations need archiving or whether normalization is generating redundant rows.
- **X API requires a paid tier.** If live posting is being considered and the X Developer Portal shows a cost requirement, confirm the tier and monthly estimate before enabling posting.
- **Any new paid API dependency is proposed.** No new paid external API should be added to the daily build without a cost review, regardless of the amount.

---

## Current Policy

- No live X API calls until cost and credential setup are explicitly confirmed.
- No LLM processing in the daily build.
- No broad paid external API dependency in the scheduled workflow.
- All current data sources (USGS, NOAA SWPC, Wikimedia, Cloudflare Radar) are accessed as free public APIs; their rate limits and terms of service govern use.
- Cloudflare Radar ingestion is optional. If `CLOUDFLARE_API_TOKEN` is not set, that source is skipped without stopping the build.

---

## Notes

Exact pricing is not hardcoded in this document. Pricing for Supabase, GitHub, X, and other services changes over time and must be checked in each provider's current documentation. This document tracks categories and review triggers, not committed budget figures.
