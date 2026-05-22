# Failure Modes and Response Procedures

## Purpose

Document the failure modes that may occur during World Pulse daily operation, classify them by severity, and define the appropriate response for each.

This document is for internal use. It does not change public display, X text, share images, or database schema.

---

## Critical Failures

These failures require immediate investigation and may require pausing dependent activities.

### Daily Build Fails for Multiple Consecutive Days

**Indicators**

- GitHub Actions workflow shows failed status on two or more consecutive scheduled runs.
- No updated `public/display/latest.json` is committed.

**Response**

1. Check GitHub Actions logs for the first failing run.
2. Identify whether the failure is in ingestion, normalization, scoring, or file generation.
3. Do not post to X (manual or automated) while the build is failing.
4. Fix the root cause and verify with a manual workflow run before resuming the schedule.

---

### Source Lineage Orphan Count > 0

**Indicators**

- Orphan count query returns a non-zero result for any ingestion run.

**Response**

1. Identify which source produced orphan rows.
2. Check whether the ingestion script wrote observations without creating a lineage record.
3. Resolve the lineage gap before running any persistence steps.
4. Do not treat the day's normalized events as fully auditable until lineage is confirmed complete.

---

### Data Date Mismatch Repeats

**Indicators**

- The data date in `public/display/latest.json` does not match UTC yesterday for two or more consecutive days.

**Response**

1. Check the `target_date` calculation logic in the daily build script.
2. Verify that the timezone offset is not producing a date-off-by-one issue.
3. If the mismatch is confirmed systematic, fix before the next scheduled run.
4. Do not post the share text or image for a mismatched date.

---

### Share Image Generation Failure

**Indicators**

- `public/share/world-pulse-latest.jpg` or `.png` is missing or has zero file size after the build.

**Response**

1. Check the image generation step in the GitHub Actions log.
2. Identify whether the failure is in data availability, template rendering, or file write.
3. Do not post to X if the image file is missing or zero-size.
4. Keep the previous day's image as the most recent public share image until generation recovers.

---

### Generated Text Contains Blocked Wording

**Indicators**

- `post_to_x.py` dry-run returns `blocked_wording: true`.
- Manual inspection finds phrases that violate the communication policy.

**Response**

1. Identify which template or scoring output introduced the blocked phrase.
2. Update the template or output formatting to remove it.
3. Verify with a fresh dry-run before considering any posting activity.

---

### Database Connection Unavailable

**Indicators**

- GitHub Actions log shows a connection error when accessing Supabase.
- The daily build cannot read raw observations or write normalized events.

**Response**

1. Check Supabase project status.
2. Verify that the `DATABASE_URL` secret in GitHub Actions is current and correct.
3. If the connection failure is a transient Supabase outage, wait and retry with a manual run.
4. If credentials have expired or the project has been paused, renew them before retrying.

---

## Monitor-Only Issues

These issues do not require immediate intervention but should be tracked and reviewed on the next review cycle.

### Short-Term API Failure

Single-day failures from USGS, NOAA SWPC, Wikimedia, or Cloudflare Radar are expected occasionally. The build is designed to continue using existing data when a non-critical source returns an error.

**Track**

- Count of API non-2xx responses per source per week.
- If a source returns non-2xx on more than three consecutive days, escalate to Critical Failure review.

---

### Temporary NOAA Data Gap

NOAA SWPC provider windows may occasionally return shorter or missing data. A single-day gap in Kp or X-ray observations is acceptable.

**Track**

- Usable days count from the weekly coverage query.
- If usable day growth stalls for more than five consecutive days, investigate the NOAA ingestion step.

---

### Small Actions Duration Increase

A modest duration increase of less than 50% of the established baseline may reflect upstream API latency or minor load changes.

**Track**

- Duration trend over 7-day and 14-day windows.
- If trend is consistently upward, investigate the slowest build step.

---

### X Dry-Run Duplicate Detection

The dry-run shows `duplicate_post: true` for a date that was already posted (or already dry-run).

**Track**

- Confirm that `.x_posted_dates.json` is being updated correctly after each dry-run.
- If duplicates appear for dates that were never posted, review the duplicate detection logic.

---

## Response Procedures

### Check GitHub Actions Logs

GitHub Actions provides step-by-step logs for each workflow run. Check the most recent run log first, then the prior run if the failure pattern spans multiple days.

### Check Generated Files

After a failed run, verify:

- `public/display/latest.json` exists and contains a parseable data date.
- Share files in `public/share/` exist and are non-zero.
- The committed data date matches UTC yesterday.

### Check DB Connectivity

Run the Supabase source coverage query from `automation_operation.md` manually to confirm the connection is available.

### Pause X Posting if Needed

If any critical failure is active:

- Do not post to X manually or via automation.
- Resume only after the build is confirmed stable.

### Keep Public Site Unchanged

Unless a visible error appears on https://worldpulse.today/, do not alter the public display during a failure investigation. The public site should reflect the last stable build.

---

## Communication Policy

- Do not publish speculative explanations about observed issues.
- Do not add public claims or descriptions during an investigation.
- Record investigation notes internally first.
- Make public-facing changes only when the issue is confirmed and the fix is verified.
- Do not reference the internal Gap score or event-level reflection details in any public communication.
