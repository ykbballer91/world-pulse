# Historical Space Weather Pageview Window Audit

## Purpose

Evaluate event-linked candidate reference pages around selected historical Space Weather dates.

## Method

Pageviews are daily aggregated. This audit does not measure real-time human response.

## May 2024 G5 geomagnetic storm sample

- Date: 2024-05-10
- Event type: geomagnetic_storm
- Source status: source recorded
- Source note: USGS summary describes the May 10, 2024 magnetic disturbance and G5 classification from NOAA SWPC context.
- Source URL: https://www.usgs.gov/index.php/programs/geomagnetism/science/may-10-2024-magnetic-disturbance-peak-dst-351-nt

| Candidate page | Baseline before event | Day 0 | Day 1 | Day 2 | Day 7 | Simple delta ratio | Note |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Geomagnetic_storm | 725.71 | 30885 | 95369 | 33255 | 2148 | 131.41 | daily aggregation only; cache miss |
| Aurora | 3201.71 | 48753 | 341117 | 166778 | 11101 | 106.54 | daily aggregation only; cache miss |
| Space_weather | 118.71 | 571 | 1405 | 944 | 201 | 11.84 | daily aggregation only; cache miss |
| Magnetosphere | 298.0 | 1823 | 9137 | 4522 | 518 | 30.66 | daily aggregation only; cache miss |
| Solar_wind | 592.0 | 3058 | 14996 | 7800 | 926 | 25.33 | daily aggregation only; cache miss |
| Sun | 8593.43 | 8996 | 10956 | 10029 | 8008 | 1.27 | daily aggregation only; cache miss |
| Space_Weather_Prediction_Center | 21.0 | 490 | 1064 | 576 | 39 | 50.67 | daily aggregation only; cache miss |
| Carrington_Event | 4981.86 | 67279 | 106040 | 49059 | 14275 | 21.29 | daily aggregation only; cache miss |
| Solar_cycle_25 | 252.43 | 1963 | 8086 | 4658 | 1050 | 32.03 | daily aggregation only; cache miss |
| May_2024_solar_storms | 0.0 | 25 | 49333 | 42721 | 10256 | not available | daily aggregation only; cache miss |

### Initial Read

- `Geomagnetic_storm` ratio 131.41; day 0 30885.
- `Aurora` ratio 106.54; day 0 48753.
- `Space_Weather_Prediction_Center` ratio 50.67; day 0 490.

### What Not To Claim

- Do not claim awareness.
- Do not claim causality.
- Do not claim prediction.
- Do not claim emergency relevance.

## October 2024 X9.0 solar flare sample

- Date: 2024-10-03
- Event type: solar_flare
- Source status: source recorded
- Source note: NASA SVS identifies an X9.0 flare from Active Region 13842 on October 3, 2024.
- Source URL: https://svs.gsfc.nasa.gov/5398

| Candidate page | Baseline before event | Day 0 | Day 1 | Day 2 | Day 7 | Simple delta ratio | Note |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Solar_flare | 626.0 | 2643 | 2316 | 1303 | 2124 | 4.22 | daily aggregation only; cache miss |
| Space_weather | 104.86 | 138 | 179 | 133 | 338 | 1.71 | daily aggregation only; cache miss |
| Solar_storm | 91.29 | 167 | 136 | 134 | 452 | 1.83 | daily aggregation only; cache miss |
| Coronal_mass_ejection | 417.57 | 1161 | 1293 | 956 | 2502 | 3.1 | daily aggregation only; cache miss |
| Solar_wind | 518.71 | 652 | 693 | 649 | 1579 | 1.34 | daily aggregation only; cache miss |
| Sun | 6810.57 | 6748 | 7121 | 7292 | 7299 | 1.07 | daily aggregation only; cache miss |
| Space_Weather_Prediction_Center | 16.71 | 50 | 87 | 167 | 89 | 9.99 | daily aggregation only; cache miss |
| Solar_cycle_25 | 178.0 | 634 | 614 | 341 | 820 | 3.56 | daily aggregation only; cache miss |
| 2024_solar_storms | 0.0 | not available | not available | not available | not available | not available | page not found or no pageview data |

### Initial Read

- `Space_Weather_Prediction_Center` ratio 9.99; day 0 50.
- `Solar_flare` ratio 4.22; day 0 2643.
- `Solar_cycle_25` ratio 3.56; day 0 634.

### What Not To Claim

- Do not claim awareness.
- Do not claim causality.
- Do not claim prediction.
- Do not claim emergency relevance.

## December 2023 X2.8 solar flare sample

- Date: 2023-12-14
- Event type: solar_flare
- Source status: source recorded
- Source note: NASA Science describes an X2.8 flare peaking on December 14, 2023.
- Source URL: https://science.nasa.gov/blogs/solar-cycle-25/2023/12/14/sun-releases-strong-solar-flare-13/

| Candidate page | Baseline before event | Day 0 | Day 1 | Day 2 | Day 7 | Simple delta ratio | Note |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Solar_flare | 984.29 | 1393 | 2353 | 3323 | 2176 | 3.38 | daily aggregation only; cache miss |
| Space_weather | 0.0 | not available | not available | not available | not available | not available | HTTP 429; retry attempts exhausted |
| Solar_storm | 0.0 | not available | not available | not available | not available | not available | HTTP 429; retry attempts exhausted |
| Coronal_mass_ejection | 0.0 | not available | not available | not available | not available | not available | HTTP 429; retry attempts exhausted |
| Solar_wind | 0.0 | not available | not available | not available | not available | not available | HTTP 429; retry attempts exhausted |
| Sun | 0.0 | not available | not available | not available | not available | not available | HTTP 429; retry attempts exhausted |
| Space_Weather_Prediction_Center | 0.0 | not available | not available | not available | not available | not available | HTTP 429; retry attempts exhausted |
| Solar_cycle_25 | 0.0 | not available | not available | not available | not available | not available | HTTP 429; retry attempts exhausted |

### Initial Read

- `Solar_flare` ratio 3.38; day 0 1393.
- `Space_weather` ratio not available; day 0 not available.
- `Solar_storm` ratio not available; day 0 not available.

### What Not To Claim

- Do not claim awareness.
- Do not claim causality.
- Do not claim prediction.
- Do not claim emergency relevance.

## September 2017 X9.3 solar flare sample

- Date: 2017-09-06
- Event type: solar_flare
- Source status: source recorded
- Source note: NASA SVS describes the September 6, 2017 X-class flare sequence observed by Solar Dynamics Observatory.
- Source URL: https://svs.gsfc.nasa.gov/12706

| Candidate page | Baseline before event | Day 0 | Day 1 | Day 2 | Day 7 | Simple delta ratio | Note |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Solar_flare | 0.0 | not available | not available | not available | not available | not available | HTTP 429; retry attempts exhausted |
| Space_weather | 0.0 | not available | not available | not available | not available | not available | HTTP 429; retry attempts exhausted |
| Solar_storm | 0.0 | not available | not available | not available | not available | not available | HTTP 429; retry attempts exhausted |
| Coronal_mass_ejection | 472.43 | 3031 | 3477 | 3025 | 830 | 7.36 | daily aggregation only; cache miss |
| Solar_wind | 584.14 | 865 | 944 | 966 | 677 | 1.65 | daily aggregation only; cache miss |
| Sun | 5724.29 | 6487 | 7488 | 6253 | 6336 | 1.31 | daily aggregation only; cache miss |
| Space_Weather_Prediction_Center | 13.29 | 108 | 119 | 72 | 21 | 8.96 | daily aggregation only; cache miss |
| Solar_cycle_24 | 182.0 | 540 | 542 | 666 | 282 | 3.66 | daily aggregation only; cache miss |

### Initial Read

- `Space_Weather_Prediction_Center` ratio 8.96; day 0 108.
- `Coronal_mass_ejection` ratio 7.36; day 0 3031.
- `Solar_cycle_24` ratio 3.66; day 0 540.

### What Not To Claim

- Do not claim awareness.
- Do not claim causality.
- Do not claim prediction.
- Do not claim emergency relevance.

## July 2012 solar eruptive event sample

- Date: 2012-07-23
- Event type: solar_flare
- Source status: source recorded
- Source note: NASA Science describes a powerful coronal mass ejection observed by STEREO-A on July 23, 2012.
- Source URL: https://science.nasa.gov/science-research/planetary-science/23jul_superstorm/

| Candidate page | Baseline before event | Day 0 | Day 1 | Day 2 | Day 7 | Simple delta ratio | Note |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| July_2012_solar_storm | 0.0 | not available | not available | not available | not available | not available | page not found or no pageview data |
| Coronal_mass_ejection | 0.0 | not available | not available | not available | not available | not available | page not found or no pageview data |
| Solar_storm | 0.0 | not available | not available | not available | not available | not available | page not found or no pageview data |
| Solar_wind | 0.0 | not available | not available | not available | not available | not available | page not found or no pageview data |
| Space_weather | 0.0 | not available | not available | not available | not available | not available | page not found or no pageview data |
| Sun | 0.0 | not available | not available | not available | not available | not available | HTTP 429; retry attempts exhausted |
| Space_Weather_Prediction_Center | 0.0 | not available | not available | not available | not available | not available | HTTP 429; retry attempts exhausted |
| Carrington_Event | 0.0 | not available | not available | not available | not available | not available | HTTP 429; retry attempts exhausted |
| Solar_cycle_24 | 0.0 | not available | not available | not available | not available | not available | HTTP 429; retry attempts exhausted |

### Initial Read

- `July_2012_solar_storm` ratio not available; day 0 not available.
- `Coronal_mass_ejection` ratio not available; day 0 not available.
- `Solar_storm` ratio not available; day 0 not available.

### What Not To Claim

- Do not claim awareness.
- Do not claim causality.
- Do not claim prediction.
- Do not claim emergency relevance.

## October 2003 X17.2 solar flare sample

- Date: 2003-10-28
- Event type: solar_flare
- Source status: source recorded
- Source note: NASA Earth Observatory describes an X17.2 flare on October 28, 2003.
- Source URL: https://earthobservatory.nasa.gov/images/3912/massive-solar-flare

| Candidate page | Baseline before event | Day 0 | Day 1 | Day 2 | Day 7 | Simple delta ratio | Note |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 2003_Halloween_solar_storms | 0.0 | not available | not available | not available | not available | not available | HTTP 429; retry attempts exhausted |
| Solar_flare | 0.0 | not available | not available | not available | not available | not available | HTTP 429; retry attempts exhausted |
| Space_weather | 0.0 | not available | not available | not available | not available | not available | HTTP 429; retry attempts exhausted |
| Solar_storm | 0.0 | not available | not available | not available | not available | not available | HTTP 429; retry attempts exhausted |
| Coronal_mass_ejection | 0.0 | not available | not available | not available | not available | not available | HTTP 429; retry attempts exhausted |
| Solar_wind | 0.0 | not available | not available | not available | not available | not available | HTTP 429; retry attempts exhausted |
| Sun | 0.0 | not available | not available | not available | not available | not available | HTTP 429; retry attempts exhausted |
| Space_Weather_Prediction_Center | 0.0 | not available | not available | not available | not available | not available | page not found or no pageview data |
| Solar_cycle_23 | 0.0 | not available | not available | not available | not available | not available | page not found or no pageview data |

### Initial Read

- `2003_Halloween_solar_storms` ratio not available; day 0 not available.
- `Solar_flare` ratio not available; day 0 not available.
- `Space_weather` ratio not available; day 0 not available.

### What Not To Claim

- Do not claim awareness.
- Do not claim causality.
- Do not claim prediction.
- Do not claim emergency relevance.

