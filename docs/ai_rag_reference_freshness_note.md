# AI/RAG Reference-Data Freshness Note

## Purpose

Explain how World Pulse can evaluate whether selected reality events appear in structured reference systems over time.

This note is internal. It is intended to organize the current Space Weather evidence before any buyer-facing material is prepared.

## Core Idea

World Pulse does not measure real-time attention.

It compares selected public reality records with later reference-system activity.

For AI/RAG use cases, the relevant question is not whether people reacted in real time. The question is whether structured reference sources show measurable activity around a source-recorded event window.

## Why This Matters for AI/RAG

AI/RAG systems depend on reference data.

Reference systems update unevenly. Some domains may show delayed or uneven reference activity after reality events. If that activity can be measured, World Pulse may support reference-data freshness review as an internal evaluation workflow.

This is useful for teams that need to understand when event-linked reference pages show measurable movement, and when reference sources remain quiet or unavailable in the selected window.

## Current Best Sample Category

Historical Space Weather appears stronger than current earthquake examples because:

- Event categories are cleaner.
- Candidate reference pages are less location-dependent.
- Pageview-window movement is more interpretable in selected cases.
- Source-recorded historical events can be audited faster than waiting for local NOAA accumulation.

The current best samples are historical, not daily production samples. NOAA snapshot accumulation should continue in parallel.

## Strongest Internal Samples

### 1. May 2024 G5 geomagnetic storm sample

- Event label: May 2024 G5 geomagnetic storm sample
- Event date: 2024-05-10
- Source status: source recorded
- Candidate pages: `Geomagnetic_storm`, `Aurora`, `Space_weather`, `Magnetosphere`, `Solar_wind`, `Space_Weather_Prediction_Center`, `Carrington_Event`, `Solar_cycle_25`, `May_2024_solar_storms`

Observed pageview movement summary:

- `Geomagnetic_storm`: simple delta ratio 131.41; day 0 views 30,885
- `Aurora`: simple delta ratio 106.54; day 0 views 48,753
- `Space_Weather_Prediction_Center`: simple delta ratio 50.67; day 0 views 490
- `Solar_cycle_25`: simple delta ratio 32.03; day 0 views 1,963

Why it is useful as internal evidence:

- The event is source-recorded and date-specific.
- Multiple event-linked reference pages show strong movement in the selected daily window.
- The candidate page set is compact and category-aligned.

What cannot be claimed:

- It cannot be used as evidence of real-time attention.
- It cannot establish causality.
- It cannot support prediction or emergency notice use.
- It cannot support market use.

### 2. October 2024 X9.0 solar flare sample

- Event label: October 2024 X9.0 solar flare sample
- Event date: 2024-10-03
- Source status: source recorded
- Candidate pages: `Solar_flare`, `Space_weather`, `Solar_storm`, `Coronal_mass_ejection`, `Solar_wind`, `Space_Weather_Prediction_Center`, `Solar_cycle_25`

Observed pageview movement summary:

- `Space_Weather_Prediction_Center`: simple delta ratio 9.99; day 0 views 50
- `Solar_flare`: simple delta ratio 4.22; day 0 views 2,643
- `Solar_cycle_25`: simple delta ratio 3.56; day 0 views 634
- `Coronal_mass_ejection`: simple delta ratio 3.10; day 0 views 1,161

Why it is useful as internal evidence:

- It provides a recent solar flare sample with readable reference-page movement.
- The candidate pages are mostly general Space Weather reference pages rather than location-specific pages.
- Only one candidate row remained unavailable in the latest dry-run.

What cannot be claimed:

- It cannot be used as evidence of real-time attention.
- It cannot establish causality.
- It cannot support prediction or emergency notice use.
- It cannot support market use.

### 3. September 2017 X9.3 solar flare sample

- Event label: September 2017 X9.3 solar flare sample
- Event date: 2017-09-06
- Source status: source recorded
- Candidate pages: `Coronal_mass_ejection`, `Solar_wind`, `Space_Weather_Prediction_Center`, `Solar_cycle_24`

Observed pageview movement summary:

- `Space_Weather_Prediction_Center`: simple delta ratio 8.96; day 0 views 108
- `Coronal_mass_ejection`: simple delta ratio 7.36; day 0 views 3,031
- `Solar_cycle_24`: simple delta ratio 3.66; day 0 views 540
- `Solar_wind`: simple delta ratio 1.65; day 0 views 865

Why it is useful as internal evidence:

- It gives an older comparison point outside the 2024 cycle.
- Several reference pages show readable movement despite some unavailable rows.
- It helps test whether the method works across different Space Weather periods.

What cannot be claimed:

- It cannot be used as evidence of real-time attention.
- It cannot establish causality.
- It cannot support prediction or emergency notice use.
- It cannot support market use.

## What World Pulse Can Claim

- Event-linked candidate pages can be identified.
- Pageview windows can be measured.
- Some historical Space Weather samples show clearer reference-page movement than earthquake samples.
- This may support reference-data freshness review as a product hypothesis.

## What World Pulse Cannot Claim

- Real-time public awareness.
- Causality.
- Prediction.
- Emergency or action relevance.
- Market relevance.
- Model quality conclusions.

## Buyer Relevance

### AI/RAG reference-data teams

The strongest use case is internal review of whether reference pages linked to source-recorded events show measurable activity in a defined window. This can help teams reason about reference-data freshness without claiming real-time response or source completeness.

### Research teams

Research teams can use the method to compare event categories, reference page sets, and daily pageview windows. Space Weather currently appears cleaner than earthquake for event-page matching because the page set is less location-dependent.

### Data journalism teams

Data journalism teams may use the method as background context when reviewing how public events later appear in structured reference systems. The method should remain source-linked and retrospective.

## Evidence Readiness

- Internal technical note: yes
- Buyer-facing proof: not yet
- Public marketing claim: not yet

Rationale: May 2024 is strong enough to anchor an internal technical note, and October 2024 / September 2017 provide supporting examples. The sample set is still too small for broader claims.

## Next Steps

- Expand historical event list to 10-15 source-recorded samples.
- Improve pageview cache/retry.
- Score examples using `docs/internal_examples_criteria.md`.
- Prepare a short private briefing only after 2-3 samples score highly.
- Keep NOAA accumulation running in parallel.
