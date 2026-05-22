# World Pulse Next 30-Day Operating Plan

## Purpose

Define what World Pulse will operate stably, accumulate, and evaluate during the next 30 days.

## Current Status

- Public daily site is live at https://worldpulse.today/
- Daily Signal Position generation is stable on GitHub Actions schedule (09:30 JST).
- X/share text and image generation is stable.
- X auto-post is dry-run only; live posting is not enabled.
- Earthquake event-level reflection is promising but not yet buyer-facing proof (Phase 2).
- Space Weather is structurally promising but needs more NOAA snapshots (Phase 3).
- DB persistence for event-page links is designed but not yet executed.
- NOAA SWPC Kp and X-ray are ingested daily but have limited provider current-window coverage (Kp ~2.4 days, X-ray ~9.2 days).

## Operating Priorities

### Priority 1: Keep Daily Build Stable

**Scope**

- Continue daily GitHub Actions execution at 09:30 JST.
- Confirm latest data date consistency.
- Monitor GitHub Actions duration for any unexpected changes.
- Verify public/share files are generated and committed.
- Preserve source_lineage completeness in all normalized events.
- Do not mix generated display files with unrelated project files.

**Why**

The public Signal Position is the foundation. Any breakdown here affects the entire observatory claim.

**How to apply**

- Monitor the daily workflow log for failures or duration spikes.
- Spot-check that `public/display/latest.json` and dated share files are created.
- Keep source_lineage fields populated so all observations remain auditable.

### Priority 2: Accumulate NOAA Snapshots

**Scope**

- Continue daily ingestion of NOAA SWPC Kp and X-ray current-window observations.
- Store each day's snapshot into local history.
- Do not overinterpret Space Weather results yet.
- Plan to rerun Space Weather dry-run after 30, 60, and 90 days of accumulation.
- Monitor for emergence of Kp >= 5 candidates (currently 0).
- Track X-ray M-class candidate count (currently 3).

**Why**

Space Weather is structurally promising, but provider current windows are short. Building local history over time is the only way to validate whether it produces stronger examples than earthquakes or internet outage observations.

**How to apply**

- Confirm daily NOAA ingestion continues in the build log.
- Preserve `.source_lineage` records for all NOAA observations.
- After 30 days, rerun `dry_run_space_weather_reflection.py --days 30` and compare example counts with current Phase 3 output.
- After 60 and 90 days, repeat the dry-run to assess trend and candidate evolution.

### Priority 3: Hold DB Persistence Until One More Review

**Scope**

- DB persistence design is complete (see `event_page_persistence_plan.md`).
- Do not execute any migration or begin storing event-page links yet.
- If executed later, persist only:
  - `registry_reviewed` candidates
  - `exists=true` pages
  - confidence `high` or `medium`
- Do not store by default:
  - heuristic fallback candidates
  - confidence `low`
  - `exists=false`
  - ambiguous location-derived candidates

**Why**

Earthquake Phase 2 evidence is promising but narrow. Storing low-confidence or heuristic candidates now would create a database of noise that is difficult to audit later. One more cycle of either stronger earthquakes or competitive category evidence (Space Weather, internet outage) should inform the persistence decision.

**How to apply**

- Keep the persistence design available but do not implement.
- Prepare a dry-run version of the migration if helpful for review, but do not commit it to main.
- After 30/60/90-day Space Weather accumulation, reassess whether to persist together or separately.

### Priority 4: Keep X Auto-Post in Dry-Run

**Scope**

- Live X posting is not enabled.
- Dry-run mode (`scripts/post_to_x.py --dry-run`) validates text generation, image generation, data date parsing, and duplicate prevention logic.
- Do not commit changes that enable live posting.
- Live posting requires separate approval and setup of:
  - X API credentials in GitHub Secrets
  - API cost and credit confirmation
  - Duplicate state management strategy
  - Media upload handling testing

**Why**

X posting introduces external service dependency and cost. Dry-run mode keeps the workflow ready while avoiding premature external engagement.

**How to apply**

- Periodically run the dry-run locally to verify the text and image match public/share files.
- Check that `post_to_x.py` correctly parses data dates and detects duplicates.
- Do not enable live posting until X API credentials and cost framework are explicitly approved.

### Priority 5: Build Commercial Evidence Slowly

**Scope**

- Do not pitch broadly yet.
- Collect strongest internal examples from each category (Earthquake, Space Weather, Internet Outage if available).
- Continue evaluating the hypothesis that AI/RAG systems benefit from reference-data freshness review.
- Strongest current evidence is internal and earthquake-focused; Space Weather will be competitive after 30-90 day accumulation.

**Why**

The gap between public Signal Position and buyer-facing commercial claim is intentional. World Pulse is an observatory, not a service claim. Forcing examples too early will lead to weak pitches; waiting until 30/60/90-day data arrive allows a cleaner story.

**How to apply**

- Document the strongest earthquake example internally (currently southern East Pacific Rise).
- After 30 days, document the strongest Space Weather examples if they emerge.
- After 60/90 days, prepare a short internal technical note on the method, limits, and evidence quality.
- Do not share or pitch examples publicly until category coverage is stable.

## What To Do This Week

- Commit `docs/noaa_snapshot_accumulation_plan.md` and any recent additions to `docs/automation_operation.md` if not yet committed.
- Create this next 30-day plan.
- Continue daily build execution and confirm no visible failures.
- Optionally prepare a dry-run version of the DB persistence migration for internal testing, but do not merge it.
- Keep X posting in dry-run mode only.
- Do not expose Gap scores publicly.
- Do not add Space Weather results to the public display.

## What To Wait For

- NOAA snapshot accumulation (30/60/90 day milestones).
- Emergence of Kp >= 5 candidates in stored snapshots (currently 0).
- Additional X-ray M-class candidates (currently 3).
- Stronger pageview-window measurement patterns in Space Weather examples.
- One additional event category (Space Weather or Internet Outage) to reach sufficient evidence for category comparison.
- Manual review before committing database persistence.

## 30-Day Review Questions

At the end of the next 30 days, ask:

- Did NOAA accumulation begin without errors?
- Are new Kp >= 5 candidates visible in accumulated snapshots?
- Did more X-ray M-class candidates emerge?
- Are Space Weather pageview windows as measurable as earthquake windows?
- Is the reference candidate registry stable without needing broad heuristic expansion?
- Does DB persistence still require one more review, or is it justified?
- Should live X posting be enabled, or should it remain dry-run?
- Is there a concrete buyer-facing example yet, or does evidence remain internal?
- Does Wikipedia remain a useful Reflection proxy, or are other reference sources necessary?
- Should another category such as Cloudflare Radar / Internet outage be reviewed next?

## Do Not Do

**Safety**

- Do not show Gap publicly.
- Do not expose internal comparison scores.
- Do not enable live X posting without explicit approval.

**Commercial**

- Do not start broad sales outreach.
- Do not use investment or trading positioning.
- Do not use emergency or safety positioning.
- Do not create buyer-facing claims about Space Weather until 30+ days of evidence accumulates.

**Data**

- Do not store heuristic event-page links by default.
- Do not store low-confidence candidates or non-existent page links.
- Do not treat Space Weather as commercially proven yet.
- Do not overwrite published snapshots in `public/share` without documentation.

**Infrastructure**

- Do not overbuild dashboards or commercial features before stronger evidence.
- Do not add public UI elements for event-level reflection.
- Do not commit persistence migrations to main before manual review.

## Suggested Review Dates

From the start of NOAA snapshot accumulation (approximately now):

- **Day 30**: Rerun Space Weather dry-run with 30 days of accumulated snapshots. Check Kp and X-ray candidate emergence. Assess whether pageview movement is becoming more interpretable. Confirm DB persistence is still deferred or proceed with narrow scope.
- **Day 60**: Rerun Space Weather dry-run with 60 days. Evaluate whether Space Weather examples are stronger than earthquake examples. Review whether the reference candidate registry is clean and stable.
- **Day 90**: Rerun Space Weather dry-run with 90 days. Decide whether Space Weather becomes a primary commercial sample category. Decide whether to execute DB persistence for reviewed links. Consider whether to add a third event category (Internet Outage) to the evaluation.

## Success Criteria for This Phase

- Daily build runs without failures for 30 consecutive days.
- NOAA snapshots accumulate without data loss or lineage breakage.
- Space Weather dry-run at day 30 shows either stronger evidence or identifies barriers.
- X posting remains ready in dry-run, with live mode still dormant.
- No public display changes are made.
- DB persistence remains designed but unexecuted.
- Commercial positioning remains internal and evidence-based, not prescriptive.
