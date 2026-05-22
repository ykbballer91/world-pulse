# Space Weather Reflection Plan

## Why Space Weather

Space Weather is a useful Phase 3 category because events are public, timestamped, and tied to a compact set of reference pages. The category is also less location-dependent than earthquakes, which may reduce candidate-page noise.

## Why It May Be Better Than Earthquake For Reflection Study

Earthquake candidates often require place-name parsing and local context review. Space Weather candidates can use a smaller domain vocabulary such as solar flare, geomagnetic storm, aurora, and space weather. That may make event-to-reference page linking easier to audit.

## Reality Sources

- NOAA SWPC Kp observations.
- NOAA SWPC X-ray flux observations.

## Candidate Event Rules

- Kp >= 5 as a geomagnetic event candidate.
- Kp >= 7 as a stronger geomagnetic candidate.
- X-ray M-class or above as a solar flare candidate.
- X-ray X-class as a stronger solar flare candidate.

## Candidate Reference Pages

Solar flare candidates:

- Core: `Solar_flare`, `Space_weather`, `Solar_storm`
- Extended: `Coronal_mass_ejection`, `Solar_wind`
- Context: `Sun`, `Space_Weather_Prediction_Center`
- Historical reference: `Carrington_Event`, `Solar_cycle_25`

Geomagnetic candidates:

- Core: `Geomagnetic_storm`, `Aurora`, `Space_weather`
- Extended: `Magnetosphere`, `Solar_wind`
- Context: `Earth%27s_magnetic_field`, `Space_Weather_Prediction_Center`
- Historical reference: `Carrington_Event`

## What Can Be Said

- Candidate events can be extracted from stored NOAA SWPC records.
- Candidate reference pages can be generated from a reviewed registry.
- Daily pageview windows can be measured for candidate pages.
- Results can be compared with earthquake Phase 2 samples.

## What Cannot Be Said

- Do not claim public awareness.
- Do not claim causality.
- Do not claim prediction.
- Do not claim emergency relevance.
- Do not claim real-world outcome from pageview movement.

## Limitations

- Stored NOAA SWPC data may be limited to provider current windows.
- The dry-run does not assume true 90-day coverage.
- Pageviews are daily aggregated and not real-time response.
- Wikipedia is only one structured reference source.
- Historical reference pages are low-confidence context unless manually reviewed.

## Current Data Availability Caveat

Before using a requested 90-day window, this phase audits the stored NOAA SWPC data range. If the stored data is shorter than 90 days, the dry-run uses only the available range and labels it accordingly.
