# World Pulse Current Strategy Index

## Purpose

This document summarizes the current strategic state of World Pulse so that future work uses the latest product definition, evidence status, and operating priorities.

## Current Product Definition

World Pulse is a Reality-Reflection Observatory.

It compares selected public reality records with activity in structured reference systems.

Current public product:

- Daily Signal Position
- Data date in UTC
- Public observation cards
- X/share generation
- No public Gap display
- No public AI/RAG claim

## Current Operating Status

- Daily build is live.
- GitHub Actions runs the daily pipeline.
- X/share text and images are generated.
- X posting is still manual.
- X auto-post exists only as dry-run.
- Share image font rendering has been hardened.
- `post_to_x.py` checks image dimensions, image file size, data date, duplicate status, and blocked wording.
- NOAA accumulation continues in the background.

## Current Methodological Status

### Earthquake Phase 2

- Useful method test.
- Event-level linking works.
- Pageview-window audit works.
- Reviewed registry exists.
- Persistence policy exists.
- Commercial readiness: promising but not strongest category.

### Space Weather Phase 3

- Current-window NOAA data was too short.
- Historical samples allowed faster evaluation.
- Historical Space Weather became the strongest current category.
- 11 events reviewed.
- 6 samples scored 10+.
- Top 3 samples are ready for private briefing use.

## Current Strongest Category

Historical Space Weather.

Why it is currently strongest:

- Cleaner candidate reference pages than earthquake.
- Less location-dependent.
- Source-recorded events available.
- Multiple high-scoring internal examples.
- Better fit for AI/RAG reference-data freshness exploration.

Top samples:

- May 2024 G5 geomagnetic storm sample
- October 2021 X1.0 solar flare sample
- December 2023 X2.8 solar flare sample

## Current Commercial Hypothesis

Primary hypothesis: AI/RAG reference-data freshness review.

Careful framing:

- AI/RAG systems depend on reference systems.
- Reference systems update unevenly.
- World Pulse can review selected event-linked reference-system activity.
- This is not yet buyer-facing proof.

Potential future forms:

- Private briefing
- Custom Reality-Reflection brief
- Reference-data freshness review
- Source-linked observation window report

## Current Evidence Status

- Internal technical note: supported
- Private briefing draft: supported
- Private slide outline: supported
- Buyer-facing proof: not yet
- Public marketing claim: not yet
- Paid product: not yet

## Current Documents by Role

| Role | Current document | Use |
| --- | --- | --- |
| Product definition / current strategy | `docs/current_strategy_index.md` | Current strategic index |
| 30-day operation | `docs/next_30_day_plan.md` | Operating plan and review questions |
| Daily operation | `docs/daily_health_metrics.md` | Daily pipeline health checks |
| Daily operation | `docs/failure_modes.md` | Failure review and response guidance |
| Daily operation | `docs/cost_monitoring.md` | Cost observation guidance |
| Stop / review rules | `docs/stop_criteria.md` | Stop rules for the project path |
| Stop / review rules | `docs/internal_examples_criteria.md` | Internal example scoring rules |
| Earthquake method validation | `docs/phase2_review.md` | Phase 2 evidence review |
| Earthquake method validation | `docs/event_page_persistence_plan.md` | Event-page persistence policy |
| Space Weather method validation | `docs/space_weather_reflection_plan.md` | Space Weather method plan |
| Space Weather method validation | `docs/noaa_snapshot_accumulation_plan.md` | NOAA accumulation plan |
| Space Weather method validation | `docs/historical_space_weather_sample_audit.md` | Historical sample audit policy |
| Space Weather method validation | `docs/historical_space_weather_expansion_notes.md` | Historical sample expansion notes |
| Space Weather method validation | `docs/historical_space_weather_scoring_notes.md` | Historical scoring notes |
| Space Weather method validation | `docs/top_space_weather_samples_review.md` | Top sample communication review |
| AI/RAG internal material | `docs/ai_rag_reference_freshness_note.md` | Technical note |
| AI/RAG internal material | `docs/ai_rag_private_briefing_skeleton.md` | Briefing skeleton |
| AI/RAG internal material | `docs/ai_rag_private_briefing_two_page_draft.md` | Two-page draft |
| AI/RAG internal material | `docs/ai_rag_private_briefing_readiness_review.md` | Readiness review |
| AI/RAG internal material | `docs/ai_rag_private_briefing_slide_outline.md` | Five-slide outline |
| AI/RAG internal material | `docs/ai_rag_private_briefing_visual_spec.md` | Visual and information design |
| AI/RAG internal material | `docs/ai_rag_private_briefing_5_slide_draft.md` | Five-slide Markdown draft |

## Current Do

- Keep daily build stable.
- Continue NOAA Kp/X-ray accumulation.
- Use historical Space Weather samples for faster internal validation.
- Keep X posting manual or dry-run only.
- Keep Gap internal.
- Prepare private briefing material only.
- Review top Space Weather samples carefully.
- Keep limitations visible near evidence.

## Current Do Not

- Do not show Gap publicly.
- Do not claim real-time attention.
- Do not claim causality.
- Do not claim prediction.
- Do not make emergency or action-use claims.
- Do not make market-use claims.
- Do not claim model-quality diagnosis.
- Do not enable live X posting yet.
- Do not run broad outreach yet.
- Do not treat the private deck as buyer-facing proof.
- Do not execute DB persistence until another review.

## Next Recommended Work

1. Commit and maintain current strategy index.
2. Finish slide style spec if not yet done.
3. Create first private slide draft only after style spec.
4. Keep NOAA accumulation running.
5. Continue daily X manual posting after dry-run.
6. Consider private 1:1 exploratory explanation only after slide draft review.
7. Delay DB persistence.
8. Delay live X auto-post.
9. Delay Cloudflare Radar / Internet observation path until after current AI/RAG path is reviewed.

## Decision Gates

### Before PPTX/PDF

- 5-slide draft exists.
- Visual spec exists.
- Limitations are visible.
- Evidence status is clear.

### Before 1:1 Exploratory Explanation

- Private deck reviewed.
- Top samples reviewed.
- No public claim language.
- No hype language.

### Before Buyer-Facing Proof

- More source-recorded samples.
- Simple charts/tables.
- Source wording review.
- Controlled feedback from at least 1-3 informed reviewers.

### Before DB Persistence

- One more review.
- Only reviewed / exists=true / high or medium confidence links.
- No heuristic links by default.

### Before Live X Auto-Post

- X API cost confirmed.
- Credentials available.
- GitHub Secrets configured.
- Duplicate state strategy ready.
- Media upload flow tested.

## Current Roadmap

- Stage 1: Public observation base — complete
- Stage 2: Earthquake method validation — complete
- Stage 3: Space Weather internal evidence — strong progress
- Stage 4: AI/RAG private briefing material — in progress
- Stage 5: Strategy index and private deck — next
- Stage 6: Controlled exploratory explanation — later
- Stage 7: Productization decision — later

## Current One-Line Summary

World Pulse is no longer just a daily observation site; it is developing into an internal evidence system for evaluating reference-data freshness, with historical Space Weather currently the strongest category for private AI/RAG-oriented explanation.
