# Event-Level Entity Linking Plan

## Why Daily Reality-Reflection Is Insufficient

Daily aggregation compares strong reality-side events with broad Wikipedia reflection for the same data date. That can show date-level movement, but it does not show whether the same event later appears in reference systems.

Event-level linking is needed to inspect whether a specific reality event has plausible reference pages that can be checked later.

## What Event-Level Reflection Means

A reality event is linked to candidate reference pages. Later, those pages can be inspected for reference activity after the event time.

This task only produces candidates. It does not measure page activity yet.

## Initial Event Types

- earthquake
- space weather
- internet outage

The first dry-run target is earthquake events.

## Candidate Page Groups

For each event, generate three candidate groups.

Core pages:

- General pages directly related to the event type
- Examples: `Earthquake`, `Seismology`, `Seismic_wave`, `Tsunami`

Context pages:

- Location, country, region, geological feature, or infrastructure context
- Examples: `Japan`, `Pacific_Ocean`, `East_Pacific_Rise`

Historical/context pages:

- Related historical pages only when the relation is direct
- Confidence should be low unless the relation is specific and clear

## Reflection Windows For Future Measurement

Future measurement windows:

- event time + 24h
- event time + 48h
- event time + 7d

No measurement is performed in this task.

## What Can Be Claimed

- Candidate reference pages can be generated for selected reality events.
- These candidates can later be checked for reference activity.

## What Cannot Be Claimed

- Do not claim public awareness.
- Do not claim emergency relevance.
- Do not claim prediction.
- Do not claim model deficiency.
- Do not treat absence from candidate pages as absence of public response.

## Known Limitations

- Candidate pages are heuristic.
- Location extraction may be imperfect.
- Wikipedia page titles may not exist.
- English Wikipedia is not globally representative.
- Reference activity may occur outside Wikipedia.
