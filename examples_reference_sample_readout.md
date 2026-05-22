# Reference Pageview Window Sample Readout

## Purpose

Evaluate whether event-level candidate pageview windows are strong enough for buyer-facing examples.

## Evaluation Criteria

- Event-linked candidate pages exist.
- Pageview movement is visible in the selected window.
- The readout avoids claims about awareness, causality, prediction, emergency relevance, or market use.
- The example can be explained to AI/RAG, research, or data journalism teams without overclaiming.

## Candidate 1: 2026-05-20 / southern East Pacific Rise

### Reality Event

- M6.6 earthquake near southern East Pacific Rise
- Event time: 2026-05-20 17:43 UTC
- Magnitude: 6.6
- Location phrase: southern East Pacific Rise

### Candidate Pages Checked

- Core: `Earthquake`, `Seismology`, `Seismic_wave`, `Tsunami`
- Context: `East_Pacific_Rise`, `Pacific_Ocean`, `Mid-ocean_ridge`
- Candidate quality: all checked pages exist after cleanup.

### Pageview Movement Summary

- `East_Pacific_Rise`: baseline 39.14, day 0 131, simple delta ratio 3.35
- `Earthquake`: baseline 1081.57, day 0 1491, simple delta ratio 1.38
- `Mid-ocean_ridge`: baseline 218.71, day 0 300, simple delta ratio 1.37
- `Tsunami`: baseline 1201.71, day 0 1334, simple delta ratio 1.11
- Later daily windows were not yet available at report time for this event date.

### Why It May Matter

This is the strongest current sample because a specific geologic context page exists and shows measurable pageview movement on the event date. It demonstrates the value of moving from date-level reflection to event-linked reference pages.

### What We Can Say

- Candidate reference pages can be generated for the event.
- The candidate pages exist after cleanup.
- Daily pageview movement can be measured for the core and context pages.
- `East_Pacific_Rise` had higher day 0 pageviews than its prior 7-day average.

### What We Cannot Say

- We cannot claim that the event caused the pageview movement.
- We cannot claim public awareness.
- We cannot claim emergency relevance.
- We cannot claim prediction.
- We cannot treat daily pageviews as real-time response.

### Buyer Suitability

- AI/RAG: Strong. Shows a concrete event-to-reference-page path and a freshness review target.
- Insurance/risk research: Medium. Geologic context is useful, but the sample needs more event categories and longer windows.
- Data journalism: Medium. The event-linked page list is explainable, but the readout needs source notes and page-title review.
- Academic/policy: Strong. Useful as a method example for studying structured reference activity after public events.

## Candidate 2: 2026-05-15 / Ōfunato, Japan

### Reality Event

- M6.7 earthquake near 49 km ESE of Ōfunato, Japan
- Event time: 2026-05-15 11:22 UTC
- Magnitude: 6.7
- Location phrase: 49 km ESE of Ōfunato, Japan

### Candidate Pages Checked

- Core: `Earthquake`, `Seismology`, `Seismic_wave`
- Context: `Japan`, `Ōfunato`, `Tōhoku_region`
- Candidate quality: all checked pages exist after cleanup, but local and regional candidates remain low confidence.

### Pageview Movement Summary

- `Earthquake`: baseline 1079.43, day 0 1010, day 1 811, day 2 841, simple delta ratio 0.82
- `Seismology`: baseline 105.86, day 0 88, day 1 94, day 2 83, simple delta ratio 0.83
- `Seismic_wave`: baseline 151.29, day 0 132, day 1 84, day 2 102, simple delta ratio 0.70
- `Japan`: baseline 11734.57, day 0 12394, day 1 9936, day 2 10586, simple delta ratio 0.94
- `Ōfunato` and `Tōhoku_region` exist but had zero measured views in the sampled daily window.

### Why It May Matter

This sample is useful as a counterexample: candidate pages exist, but the measured pageview window does not show a strong event-linked movement pattern. That helps define quality thresholds before DB persistence.

### What We Can Say

- Candidate pages can be generated and checked.
- The candidate pages exist.
- Pageview windows can be computed for core and context pages.
- This example does not currently provide a strong buyer-facing reference movement story.

### What We Cannot Say

- We cannot claim that low movement means no public response.
- We cannot claim that Wikipedia is the right reflection source for this event.
- We cannot claim emergency relevance.
- We cannot claim prediction.

### Buyer Suitability

- AI/RAG: Medium. Useful for freshness review mechanics, weaker as a sample story.
- Insurance/risk research: Medium. Event and location are clear, but the reference-page movement is weak.
- Data journalism: Low to medium. The data is explainable, but it does not carry a strong reference activity signal.
- Academic/policy: Medium. Useful for method calibration and limits.

## Candidate 3: 2026-05-14 / Tual, Indonesia

### Reality Event

- M6.2 earthquake near 271 km WSW of Tual, Indonesia
- Event time: 2026-05-14 17:53 UTC
- Magnitude: 6.2
- Location phrase: 271 km WSW of Tual, Indonesia

### Candidate Pages Checked

- Core: `Earthquake`, `Seismology`, `Seismic_wave`
- Context: `Indonesia`, `Tual`
- Candidate quality: all checked pages exist after cleanup, with `Tual` remaining low confidence.

### Pageview Movement Summary

- `Earthquake`: baseline 1087.57, day 0 997, day 1 1010, day 2 811, simple delta ratio 0.86
- `Seismology`: baseline 106.14, day 0 100, day 1 88, day 2 94, simple delta ratio 0.89
- `Seismic_wave`: baseline 150.86, day 0 163, day 1 132, day 2 84, simple delta ratio 0.84
- `Indonesia` and `Tual` exist but had zero measured views in the sampled daily window.

### Why It May Matter

This sample shows that existence checks alone are not enough. The event can be linked to plausible pages, but the pageview window does not yet support a strong event-specific reflection readout.

### What We Can Say

- Candidate reference pages can be generated and checked.
- Pageview windows can be computed.
- The current page set does not provide strong pageview movement for this event.

### What We Cannot Say

- We cannot claim absence of reflection outside Wikipedia.
- We cannot claim public awareness.
- We cannot claim emergency relevance.
- We cannot claim prediction.

### Buyer Suitability

- AI/RAG: Medium. Useful for process demonstration, not strong enough as the lead example.
- Insurance/risk research: Low to medium. Event-level linking works, but measured page movement is weak.
- Data journalism: Low. The sample does not yet produce a clear reference activity pattern.
- Academic/policy: Medium. Useful for documenting limitations.

## Overall Verdict

**(b) promising but needs stronger evidence**

The dry-run now proves that event-level candidate generation, page existence checks, and pageview-window measurement are technically feasible. The southern East Pacific Rise case is the strongest sample because it has a specific context page with measurable movement. The Japan and Indonesia cases are more useful for calibration than for buyer-facing demonstration.

## Next Step

- Build a page title resolver with reviewed replacements and confidence policy.
- Add more event categories after earthquake candidates are stable.
- Expand reference sources beyond Wikipedia before making stronger buyer-facing examples.
- Design DB persistence only after candidate quality rules and measurement windows are stable.
