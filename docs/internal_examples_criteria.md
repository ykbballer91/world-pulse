# Internal Examples Quality Criteria

## Purpose

Define how World Pulse evaluates internal Reality–Reflection examples before considering them for any form of commercial discussion.

This document is for internal use. It does not change the public display, database schema, or X posting behavior.

---

## Background

World Pulse generates internal examples by linking reality events (Earthquake, Space Weather) to candidate reference pages, then measuring pageview-window movement around those events. These examples demonstrate the method. They do not demonstrate causality, and they are not forecasts.

Before an internal example is considered for any external or commercial discussion, it should be evaluated using the criteria below.

---

## Evaluation Dimensions

Each dimension is scored 0 to 2.

### 1. Reality Event Clarity

**0** — The event is ambiguous, undated, or drawn from a low-confidence source.  
**1** — The event is clearly sourced and timestamped but lacks supporting context.  
**2** — The event has a clear timestamp, source, magnitude or type indicator, and is unambiguous in its category.

---

### 2. Candidate Page Existence

**0** — No candidate reference page was found or all candidates are `exists=false`.  
**1** — At least one candidate page exists but is provisional or low-confidence.  
**2** — The primary candidate page is `registry_reviewed`, `exists=true`, and confidence is high or medium.

---

### 3. Pageview Movement Clarity

**0** — No measurable change in pageview counts around the event window.  
**1** — A change is visible but small and not clearly above baseline noise.  
**2** — The change is above baseline and the window aligns with the event timing in a legible way.

---

### 4. Lag Measurability

**0** — No lag can be measured because reference-data publication date is unavailable.  
**1** — Lag can be estimated but the estimate has low confidence.  
**2** — Lag between the reality event date and observable reference-data change is measurable with reasonable confidence.

---

### 5. Political and Religious Neutrality

**0** — The event involves politically sensitive territory, religious framing, or content that carries significant communication difficulty in international contexts.  
**1** — The event is mostly neutral but has some potential for interpretive disagreement.  
**2** — The event is clearly neutral: a geological, atmospheric, or astrophysical observation without political or religious framing.

---

### 6. Misinterpretation Issue

**0** — The example is highly prone to being read as a prediction, a causal claim, or an application to financial or safety decisions.  
**1** — The example could be misread in certain contexts without careful framing.  
**2** — The example is clearly presentable within the four World Pulse principles: no prediction, no escalation, no investment or safety use, and no framing of the Gap as a failure indicator.

---

## Scoring Guide

| Total Score | Status |
|-------------|--------|
| 10–12 | Potentially presentable after internal review |
| 7–9 | Internal use only |
| 0–6 | Not suitable; do not present externally |

---

## Notes

**Movement is not causality.**  
Pageview changes observed around an event window may reflect many things. World Pulse does not claim that the event caused the change.

**Pageviews are not immediate public awareness.**  
Wikipedia daily pageviews are aggregated and delayed. They reflect reference-system activity, not real-time public response.

**Examples are not forecasts.**  
No internal example demonstrates prediction of future events. Examples show only retrospective measurement.

**Examples are not emergency notices.**  
No example should be read or presented as a safety-relevant observation.

**Examples are not market signals.**  
No example should be connected to investment, trading, or financial positioning.

---

## Re-Scoring Existing Examples

### Earthquake Phase 2

Existing earthquake examples from Phase 2 should be scored using the criteria above. The southern East Pacific Rise example is currently the strongest candidate. Other earthquake examples may score lower due to heuristic fallback candidates or weak pageview movement.

Scoring should be done before any external or commercial discussion of Phase 2 evidence.

### Space Weather Phase 3

Space Weather examples should be scored only after sufficient NOAA snapshot accumulation (at minimum 30 days). Current examples are provisional dry-run output and should not be scored formally until candidate quality stabilizes.

Re-score at:
- 30 days after accumulation start
- 60 days after accumulation start
- 90 days after accumulation start

### Commercial Use Threshold

No example should be used in any buyer-facing context until it meets the scoring threshold of 10–12 and has been reviewed against the communication policy in `failure_modes.md`.
