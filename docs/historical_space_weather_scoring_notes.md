# Historical Space Weather Scoring Notes

## Purpose

Record how the expanded historical Space Weather samples were scored against `docs/internal_examples_criteria.md`.

This is an internal evaluation note. It does not change public display, database schema, X posting, share images, or the daily scoring algorithm.

## Scoring Method

Each sample was scored from 0 to 2 across six dimensions:

- Reality event clarity
- Candidate page existence
- Pageview movement clarity
- Lag measurability
- Political/religious neutrality
- Misinterpretation issue

The total score maps to:

- 10-12: potentially presentable after review
- 7-9: internal use only
- 0-6: not suitable

## Why Historical Samples Are Being Used

Current local NOAA snapshot coverage is short. Historical samples allow faster review of whether source-recorded Space Weather events can be linked to reference pages with measurable daily pageview movement.

Historical samples do not replace NOAA accumulation. They are a faster internal research path while accumulation continues.

## Strongest Samples

The strongest samples in the current 11-event set are:

1. May 2024 G5 geomagnetic storm sample: score 12
2. October 2021 X1.0 solar flare sample: score 12
3. December 2023 X2.8 solar flare sample: score 12
4. October 2024 X9.0 solar flare sample: score 11
5. February 2024 X6.3 solar flare sample: score 11
6. September 2017 X9.3 solar flare sample: score 11

These samples show readable pageview movement and have source-recorded event labels.

## Weak Samples

The weaker samples are:

- May 2024 X8.7 solar flare sample: readable pages, but no clear movement in the selected window.
- April 2022 X2.2 solar flare sample: limited readable rows and weak movement.
- September 2017 X8.2 solar flare sample: not readable in this run.
- July 2012 solar eruptive event sample: not readable in this run.
- October 2003 X17.2 solar flare sample: not readable in this run.

The older samples are source-recorded, but the current Wikimedia daily pageview audit does not provide enough readable rows for them.

## Limitations

- Pageview movement is not causality.
- Pageviews are daily aggregated reference-system activity, not real-time public response.
- Some rows remain unavailable due to source availability or request limits.
- Historical events may have richer reference context than ordinary daily samples.
- Source notes still need human review before any private briefing.

## AI/RAG Technical Note Status

The AI/RAG reference-data freshness note can be strengthened. The current scoring provides enough internal evidence to support an internal technical note centered on Space Weather.

Buyer-facing proof is still premature. The current next step is to review the high-scoring samples against source notes and communication policy.

## Private Briefing Skeleton

A private briefing skeleton is justified after internal review if it stays narrow:

- Explain the method.
- Show two or three high-scoring Space Weather examples.
- State limits clearly.
- Avoid claims about causality, real-time attention, prediction, emergency notice use, or market use.

No public marketing claim should be made yet.
