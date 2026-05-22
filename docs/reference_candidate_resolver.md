# Reference Candidate Resolver

## Purpose

The resolver separates reviewed candidate page rules from heuristic location parsing.

Phase 2.4 keeps this as a file-only dry run. It does not change the database, public UI, scoring, share images, X text, or GitHub Actions.

## Registry File

The reviewed registry lives at:

```text
reference_candidate_registry.json
```

Each entry includes:

- `event_type`
- `match_pattern`
- `candidate_page`
- `candidate_group`
- `confidence`
- `review_status`
- `reason`

Optional `conditions` can narrow a rule. The initial use is `Tsunami`, which is only added for larger ocean-region earthquake events.

## Initial Scope

The first registry covers earthquake samples used in the Phase 2 dry runs.

Reviewed core pages:

- `Earthquake`
- `Seismology`
- `Seismic_wave`
- `Tsunami` with conditions

Reviewed context pages:

- `East_Pacific_Rise`
- `Pacific_Ocean`
- `Japan`
- `Ōfunato`
- `Tōhoku_region`
- `Indonesia`
- `Papua_New_Guinea`
- `Peru`
- `Turkey`

## Resolver Order

1. Apply reviewed registry matches.
2. Apply existing heuristic candidates as fallback.
3. De-duplicate by page title.
4. Preserve confidence and reason in dry-run output.

Registry-derived candidates include `registry` in their reason text.

## Review Policy

- `reviewed` means the page rule is suitable for dry-run reporting.
- `provisional` means the page can appear in dry runs, but needs more review before database storage.
- Low-confidence local candidates remain visible only when explicitly allowed for the current dry-run scope.

## What This Does Not Claim

- It does not claim public awareness.
- It does not claim emergency relevance.
- It does not claim prediction.
- It does not make the candidate pages final.

## Next Step

If the dry-run remains useful, the next step is to design storage for reviewed event-page candidates and pageview-window measurements.
