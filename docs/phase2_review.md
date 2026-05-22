# Phase 2 Review: Reality-Reflection Evidence Readiness

## Purpose

Review whether Phase 2 evidence is strong enough to justify database persistence, commercial sample preparation, or further event-category expansion.

This document is for internal decision-making. It does not change scoring, public display, database schema, X text, share images, or GitHub Actions.

## What Phase 2 Added

Phase 2 added a dry-run path from reality events to reference-system measurements:

- Event-level candidate reference pages.
- Page existence checks for candidate pages.
- Pageview-window dry-runs around selected event dates.
- Candidate quality cleanup for generated page titles.
- A reviewed candidate resolver backed by `reference_candidate_registry.json`.
- A persistence policy that separates reviewed registry links from heuristic fallback links.

## Evidence Improved

The evidence base is materially stronger than the earlier date-level Reality-Reflection comparison.

- Candidate pages can now be generated at the individual event level.
- Broken page titles were reduced through cleanup rules and reviewed replacements.
- Registry-derived candidates now dominate the dry-run output.
- Page existence checks work for the selected candidate pages.
- Pageview-window measurement works on selected core and context pages.
- The southern East Pacific Rise sample is currently the strongest example because `East_Pacific_Rise` exists and shows measurable pageview movement in the selected window.

## Still Weak

The current evidence is promising, but it is not yet strong enough as buyer-facing proof.

- Pageview movement is not causality.
- Earthquake events may be a weaker category for reference reflection than space weather or internet outage observations.
- Heuristic fallback candidates remain in the dry-run output.
- Wikipedia-only reflection is limited and should not be treated as the full reference-system picture.
- Some samples demonstrate the mechanics but do not produce a strong event-specific reference movement story.
- The current sample can support internal evaluation, but it needs stronger category coverage and more stable reviewed links before commercial presentation.

## Persistence Readiness

Phase 2.5 classified the current 47 event-page candidates as follows:

- Store by default: 36
- Hold for review: 3
- Exclude: 8

Initial database persistence should include only links that meet all of these conditions:

- `registry_reviewed`
- `exists=true`
- confidence `high` or `medium`

Initial persistence should not include:

- heuristic fallback candidates
- confidence `low`
- `exists=false`
- ambiguous location-derived candidates

Provisional registry links and historical/context candidates should remain dry-run-only until reviewed.

## Commercial Readiness

Verdict: **(b) promising but needs stronger evidence**

Reasoning:

- The method is now explainable at the event level.
- The southern East Pacific Rise case is a credible internal sample.
- The pageview-window workflow is technically feasible.
- Candidate quality is improving through the reviewed resolver.
- However, the current evidence set is still narrow, Wikipedia-only, and strongest for one sample rather than across event types.

This is enough to justify a controlled persistence step for reviewed links, but not enough to package as a polished buyer-facing sample.

## Recommended Next Step

1. **Database persistence for reviewed links only**

   Persist only `registry_reviewed`, `exists=true`, high/medium-confidence event-page links. Store pageview-window measurements only for those persisted links.

2. **Add one more event category**

   Prioritize space weather or internet outage observations. Either category may produce cleaner reference-system behavior than earthquake events.

3. **Build a short internal technical note for AI/RAG reference-data freshness**

   Use the current Phase 2 artifacts to explain the method, limits, and why event-level links are necessary.

4. **Keep event-level reflection out of public display for now**

   Public UI should remain Signal Position. Event-level reflection should stay internal until persistence and category coverage are stronger.

## What Not To Do

- Do not show Gap publicly.
- Do not claim awareness.
- Do not claim causality.
- Do not sell to trading or investment use.
- Do not store heuristic candidates by default.
- Do not treat Wikipedia Pageviews as a complete reference-system measure.
- Do not expose event-level reflection publicly yet.

## Decision

Proceed with a narrow database persistence design for reviewed event-page links only, while planning one additional event category. The persistence step should be scoped, reversible, and limited to audited candidates. Event-category expansion should follow immediately after the first persistence pass so the evidence base does not remain earthquake-only.
