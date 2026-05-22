# Stop Criteria

## Purpose

Define the conditions under which World Pulse, a specific feature, or a specific category should be paused or discontinued. These criteria are for internal decision-making.

This document does not change any public display, database schema, scripts, or GitHub Actions.

---

## Project-Level Review Criteria

The following conditions would trigger a project-level review of whether to continue operating World Pulse.

- **90 days pass without stronger commercial evidence.** If, after 90 days of NOAA accumulation and internal scoring, no internal example reaches the threshold in `internal_examples_criteria.md`, the commercial hypothesis needs to be reassessed.
- **Repeated communication policy concern.** If the scoring or output design repeatedly produces text or imagery that approaches the boundary of the four operating principles, a structural review is needed before continuing.
- **Operating cost becomes disproportionate.** If Supabase, GitHub Actions, API costs, or future service costs exceed a reasonable small-project range without a clear commercial path, a cost-benefit review should occur.
- **Daily build cannot be maintained.** If the required infrastructure (Supabase, GitHub Actions, Wikimedia API) becomes unavailable or prohibitively unstable, and recovery is not feasible within a reasonable timeframe, the project should be put on hold until stable infrastructure is available.

---

## Feature-Level Stop Criteria

### X Auto-Post Live

Pause or disable live X posting if:

- A post is published with incorrect data date, blocked wording, or a missing or corrupted image.
- The duplicate prevention mechanism produces a known false negative (posts the same date twice).
- X API credentials are expired or revoked and cannot be renewed promptly.

### Daily Build

Pause the daily build schedule if:

- Two or more consecutive runs fail and the root cause is not identified.
- The database connection is unavailable and cannot be restored within a reasonable timeframe.
- Source lineage orphan counts recur after a confirmed fix, suggesting a structural issue in ingestion.

### Share Image and Text Generation

Pause X posting (manual or automated) if:

- Image generation fails for two or more consecutive builds.
- Generated text includes content that requires review before public posting.
- The data date in generated text does not match UTC yesterday consistently.

### DB Persistence

Do not execute DB persistence migration if:

- A review of the reviewed candidate registry reveals quality has not improved since the last review.
- Heuristic fallback candidates would need to be included to reach a meaningful event count.
- Low-confidence or non-existent page links would need to be stored to build a useful result set.

---

## Category-Level Stop Criteria

### Earthquake

Pause Earthquake Reality–Reflection evaluation if:

- No earthquake example reaches a score of 7 or above after full scoring (see `internal_examples_criteria.md`).
- The candidate reference page registry cannot be expanded beyond the current set without introducing high-noise heuristic candidates.
- Pageview-window movement for earthquake candidates remains consistently below baseline across multiple independent test runs.

The Earthquake category may be retained as a reference baseline for comparison even if it is not the primary commercial sample category.

### Space Weather

Pause Space Weather evaluation if:

- After 90 days of NOAA accumulation, Kp >= 5 candidates and X-ray M-class candidates remain sparse.
- Pageview-window measurement for Space Weather candidate pages does not produce more interpretable results than earthquake examples.
- Wikipedia is not a useful reflection proxy for Space Weather events, and no alternative reference source is available.

### Internet Outage (Cloudflare Radar)

Do not begin Internet Outage category evaluation unless:

- Cloudflare Radar ingestion is confirmed stable.
- A category design exists that meets the communication policy (no political framing, no safety or financial implication).

---

## Restart Criteria

Any paused feature or category may be restarted when all of the following are true:

1. The reason for pausing is understood and documented.
2. A fix or structural change has been designed and tested in a dry-run environment.
3. The dry-run result passes without blocked wording, duplicate issues, or lineage gaps.
4. A manual review approves the restart before resuming the schedule or pipeline.

Restart decisions should be recorded in an internal note, not committed to the repository unless they represent a structural change.

---

## What Not To Do When Stopping

- Do not remove public display files or alter https://worldpulse.today/ content as part of a feature stop.
- Do not delete database records unless a formal data cleanup plan is approved.
- Do not announce the stop publicly unless the stop affects the public Signal Position display.
- Do not treat a category pause as a permanent exclusion; retain the framework for future reactivation.
