# Historical Space Weather Sample Readout

## Purpose

Evaluate whether historical Space Weather events produce clearer reference-page movement than current-window samples.

## Candidate Summary

- Events evaluated: 6
- Pageview windows use daily aggregation.
- Cache/retry is enabled in the audit script for reproducibility.

## Strongest Samples

1. May 2024 G5 geomagnetic storm sample — strongest ratio 131.41
2. October 2024 X9.0 solar flare sample — strongest ratio 9.99
3. September 2017 X9.3 solar flare sample — strongest ratio 8.96

## Samples With Weak Movement

- July 2012 solar eruptive event sample
- October 2003 X17.2 solar flare sample

## Samples With Unavailable Page Rows

- October 2024 X9.0 solar flare sample: 1 unavailable rows
- December 2023 X2.8 solar flare sample: 7 unavailable rows
- September 2017 X9.3 solar flare sample: 3 unavailable rows
- July 2012 solar eruptive event sample: 9 unavailable rows
- October 2003 X17.2 solar flare sample: 9 unavailable rows

## May 2024 G5 geomagnetic storm sample

- Date: 2024-05-10
- Event type: geomagnetic_storm
- Source status: source recorded

### Strongest Moving Pages
- `Geomagnetic_storm`: ratio 131.41; day 0 30885
- `Aurora`: ratio 106.54; day 0 48753
- `Space_Weather_Prediction_Center`: ratio 50.67; day 0 490
- `Solar_cycle_25`: ratio 32.03; day 0 1963

### Pages With No Clear Movement
- `May_2024_solar_storms`: ratio not available

### Interpretability

The event-linked page set can be reviewed, but pageview movement still needs source notes and category comparison.

### Buyer Suitability

- AI/RAG: useful if source-verified event pages show clear movement.
- Research: useful for comparing event categories and reference systems.
- Data journalism: useful only with careful source context.

## October 2024 X9.0 solar flare sample

- Date: 2024-10-03
- Event type: solar_flare
- Source status: source recorded

### Strongest Moving Pages
- `Space_Weather_Prediction_Center`: ratio 9.99; day 0 50
- `Solar_flare`: ratio 4.22; day 0 2643
- `Solar_cycle_25`: ratio 3.56; day 0 634
- `Coronal_mass_ejection`: ratio 3.1; day 0 1161

### Pages With No Clear Movement
- `Sun`: ratio 1.07
- `2024_solar_storms`: ratio not available

### Interpretability

The event-linked page set can be reviewed, but pageview movement still needs source notes and category comparison.

### Buyer Suitability

- AI/RAG: useful if source-verified event pages show clear movement.
- Research: useful for comparing event categories and reference systems.
- Data journalism: useful only with careful source context.

## December 2023 X2.8 solar flare sample

- Date: 2023-12-14
- Event type: solar_flare
- Source status: source recorded

### Strongest Moving Pages
- `Solar_flare`: ratio 3.38; day 0 1393
- `Space_weather`: ratio not available; day 0 not available
- `Solar_storm`: ratio not available; day 0 not available
- `Coronal_mass_ejection`: ratio not available; day 0 not available

### Pages With No Clear Movement
- `Space_weather`: ratio not available
- `Solar_storm`: ratio not available
- `Coronal_mass_ejection`: ratio not available
- `Solar_wind`: ratio not available

### Interpretability

The event-linked page set can be reviewed, but pageview movement still needs source notes and category comparison.

### Buyer Suitability

- AI/RAG: useful if source-verified event pages show clear movement.
- Research: useful for comparing event categories and reference systems.
- Data journalism: useful only with careful source context.

## September 2017 X9.3 solar flare sample

- Date: 2017-09-06
- Event type: solar_flare
- Source status: source recorded

### Strongest Moving Pages
- `Space_Weather_Prediction_Center`: ratio 8.96; day 0 108
- `Coronal_mass_ejection`: ratio 7.36; day 0 3031
- `Solar_cycle_24`: ratio 3.66; day 0 540
- `Solar_wind`: ratio 1.65; day 0 865

### Pages With No Clear Movement
- `Solar_flare`: ratio not available
- `Space_weather`: ratio not available
- `Solar_storm`: ratio not available

### Interpretability

The event-linked page set can be reviewed, but pageview movement still needs source notes and category comparison.

### Buyer Suitability

- AI/RAG: useful if source-verified event pages show clear movement.
- Research: useful for comparing event categories and reference systems.
- Data journalism: useful only with careful source context.

## July 2012 solar eruptive event sample

- Date: 2012-07-23
- Event type: solar_flare
- Source status: source recorded

### Strongest Moving Pages
- `July_2012_solar_storm`: ratio not available; day 0 not available
- `Coronal_mass_ejection`: ratio not available; day 0 not available
- `Solar_storm`: ratio not available; day 0 not available
- `Solar_wind`: ratio not available; day 0 not available

### Pages With No Clear Movement
- `July_2012_solar_storm`: ratio not available
- `Coronal_mass_ejection`: ratio not available
- `Solar_storm`: ratio not available
- `Solar_wind`: ratio not available

### Interpretability

The event-linked page set can be reviewed, but pageview movement still needs source notes and category comparison.

### Buyer Suitability

- AI/RAG: useful if source-verified event pages show clear movement.
- Research: useful for comparing event categories and reference systems.
- Data journalism: useful only with careful source context.

## October 2003 X17.2 solar flare sample

- Date: 2003-10-28
- Event type: solar_flare
- Source status: source recorded

### Strongest Moving Pages
- `2003_Halloween_solar_storms`: ratio not available; day 0 not available
- `Solar_flare`: ratio not available; day 0 not available
- `Space_weather`: ratio not available; day 0 not available
- `Solar_storm`: ratio not available; day 0 not available

### Pages With No Clear Movement
- `2003_Halloween_solar_storms`: ratio not available
- `Solar_flare`: ratio not available
- `Space_weather`: ratio not available
- `Solar_storm`: ratio not available

### Interpretability

The event-linked page set can be reviewed, but pageview movement still needs source notes and category comparison.

### Buyer Suitability

- AI/RAG: useful if source-verified event pages show clear movement.
- Research: useful for comparing event categories and reference systems.
- Data journalism: useful only with careful source context.

## Comparison With Current Space Weather Dry Run

- Historical sampling reduces the wait for first evidence review.
- It provides richer pageview windows than the short current-window NOAA store.
- It supports reference-data freshness examples if the selected events are source-verified.

## Commercial Readiness

Verdict: **(a) strong enough for internal technical note**

The historical samples are more useful than the current-window sample for speed. May 2024 remains the strongest sample in this run, while older samples need a source-compatible pageview strategy.

## Recommended Next Step

- Source-verify more events.
- Expand the event list to 10 if the next review needs broader coverage.
- Prepare an AI/RAG technical note only after the expanded review.
- Keep NOAA snapshot accumulation running in parallel.
