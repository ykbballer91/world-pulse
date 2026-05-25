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
| Geomagnetic_storm | 725.71 | 30885 | 95369 | 33255 | 2148 | 131.41 | daily aggregation only; cache hit |
| Aurora | 3201.71 | 48753 | 341117 | 166778 | 11101 | 106.54 | daily aggregation only; cache hit |
| Space_weather | 118.71 | 571 | 1405 | 944 | 201 | 11.84 | daily aggregation only; cache hit |
| Magnetosphere | 298.0 | 1823 | 9137 | 4522 | 518 | 30.66 | daily aggregation only; cache hit |
| Solar_wind | 592.0 | 3058 | 14996 | 7800 | 926 | 25.33 | daily aggregation only; cache hit |
| Sun | 8593.43 | 8996 | 10956 | 10029 | 8008 | 1.27 | daily aggregation only; cache hit |
| Space_Weather_Prediction_Center | 21.0 | 490 | 1064 | 576 | 39 | 50.67 | daily aggregation only; cache hit |
| Carrington_Event | 4981.86 | 67279 | 106040 | 49059 | 14275 | 21.29 | daily aggregation only; cache hit |
| Solar_cycle_25 | 252.43 | 1963 | 8086 | 4658 | 1050 | 32.03 | daily aggregation only; cache hit |
| May_2024_solar_storms | 0.0 | 25 | 49333 | 42721 | 10256 | not available | daily aggregation only; cache hit |

### Initial Read

- `Geomagnetic_storm` ratio 131.41; day 0 30885.
- `Aurora` ratio 106.54; day 0 48753.
- `Space_Weather_Prediction_Center` ratio 50.67; day 0 490.

### What Not To Claim

- Do not claim awareness.
- Do not claim causality.
- Do not claim prediction.
- Do not claim emergency relevance.

## May 2024 X8.7 solar flare sample

- Date: 2024-05-14
- Event type: solar_flare
- Source status: source recorded
- Source note: NASA SVS describes the May 14, 2024 X8.7 flare as the largest flare of Solar Cycle 25 at that time.
- Source URL: https://svs.gsfc.nasa.gov/14592

| Candidate page | Baseline before event | Day 0 | Day 1 | Day 2 | Day 7 | Simple delta ratio | Note |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Solar_flare | 9441.14 | 4738 | 4198 | 2688 | 1167 | 0.5 | daily aggregation only; cache miss |
| Space_weather | 553.29 | 329 | 293 | 221 | 112 | 0.59 | daily aggregation only; cache miss |
| Solar_storm | 2750.0 | 1131 | 829 | 619 | 168 | 0.41 | daily aggregation only; cache miss |
| Coronal_mass_ejection | 6550.57 | 2728 | 2465 | 1640 | 911 | 0.42 | daily aggregation only; cache miss |
| Solar_wind | 4441.71 | 1791 | 1316 | 1081 | 748 | 0.4 | daily aggregation only; cache miss |
| Sun | 9072.57 | 11662 | 8934 | 8371 | 7833 | 1.29 | daily aggregation only; cache miss |
| Space_Weather_Prediction_Center | 353.86 | 134 | 72 | 62 | 25 | 0.38 | daily aggregation only; cache miss |
| Solar_cycle_25 | 2788.0 | 2054 | 1716 | 1250 | 432 | 0.74 | daily aggregation only; cache miss |
| May_2024_solar_storms | 18951.0 | 17261 | 13864 | 11695 | 2383 | 0.91 | daily aggregation only; cache miss |

### Initial Read

- `Sun` ratio 1.29; day 0 11662.
- `May_2024_solar_storms` ratio 0.91; day 0 17261.
- `Solar_cycle_25` ratio 0.74; day 0 2054.

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
| Solar_flare | 626.0 | 2643 | 2316 | 1303 | 2124 | 4.22 | daily aggregation only; cache hit |
| Space_weather | 104.86 | 138 | 179 | 133 | 338 | 1.71 | daily aggregation only; cache hit |
| Solar_storm | 91.29 | 167 | 136 | 134 | 452 | 1.83 | daily aggregation only; cache hit |
| Coronal_mass_ejection | 417.57 | 1161 | 1293 | 956 | 2502 | 3.1 | daily aggregation only; cache hit |
| Solar_wind | 518.71 | 652 | 693 | 649 | 1579 | 1.34 | daily aggregation only; cache hit |
| Sun | 6810.57 | 6748 | 7121 | 7292 | 7299 | 1.07 | daily aggregation only; cache hit |
| Space_Weather_Prediction_Center | 16.71 | 50 | 87 | 167 | 89 | 9.99 | daily aggregation only; cache hit |
| Solar_cycle_25 | 178.0 | 634 | 614 | 341 | 820 | 3.56 | daily aggregation only; cache hit |
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

## February 2024 X6.3 solar flare sample

- Date: 2024-02-22
- Event type: solar_flare
- Source status: source recorded
- Source note: NASA SVS describes an X6.3 flare at Active Region 13590 on February 22, 2024.
- Source URL: https://svs.gsfc.nasa.gov/5233/

| Candidate page | Baseline before event | Day 0 | Day 1 | Day 2 | Day 7 | Simple delta ratio | Note |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Solar_flare | 0.0 | not available | not available | not available | not available | not available | HTTP 429; retry attempts exhausted |
| Space_weather | 0.0 | not available | not available | not available | not available | not available | HTTP 429; retry attempts exhausted |
| Solar_storm | 343.14 | 406 | 341 | 397 | 566 | 1.18 | daily aggregation only; cache miss |
| Coronal_mass_ejection | 504.29 | 1045 | 1186 | 728 | 500 | 2.35 | daily aggregation only; cache miss |
| Solar_wind | 560.29 | 618 | 627 | 514 | 561 | 1.12 | daily aggregation only; cache miss |
| Sun | 9197.86 | 9530 | 9616 | 9671 | 10062 | 1.05 | daily aggregation only; cache miss |
| Space_Weather_Prediction_Center | 9.14 | 90 | 62 | 38 | 12 | 9.84 | daily aggregation only; cache miss |
| Solar_cycle_25 | 194.29 | 425 | 576 | 276 | 232 | 2.96 | daily aggregation only; cache miss |

### Initial Read

- `Space_Weather_Prediction_Center` ratio 9.84; day 0 90.
- `Solar_cycle_25` ratio 2.96; day 0 425.
- `Coronal_mass_ejection` ratio 2.35; day 0 1045.

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
| Solar_flare | 984.29 | 1393 | 2353 | 3323 | 2176 | 3.38 | daily aggregation only; cache hit |
| Space_weather | 119.14 | 130 | 131 | 108 | 108 | 1.1 | daily aggregation only; cache miss |
| Solar_storm | 621.43 | 480 | 419 | 438 | 575 | 0.77 | daily aggregation only; cache miss |
| Coronal_mass_ejection | 670.29 | 661 | 1212 | 1333 | 613 | 1.99 | daily aggregation only; cache miss |
| Solar_wind | 848.43 | 879 | 916 | 666 | 789 | 1.08 | daily aggregation only; cache miss |
| Sun | 0.0 | not available | not available | not available | not available | not available | HTTP 429; retry attempts exhausted |
| Space_Weather_Prediction_Center | 0.0 | not available | not available | not available | not available | not available | HTTP 429; retry attempts exhausted |
| Solar_cycle_25 | 0.0 | not available | not available | not available | not available | not available | HTTP 429; retry attempts exhausted |

### Initial Read

- `Solar_flare` ratio 3.38; day 0 1393.
- `Coronal_mass_ejection` ratio 1.99; day 0 661.
- `Space_weather` ratio 1.1; day 0 130.

### What Not To Claim

- Do not claim awareness.
- Do not claim causality.
- Do not claim prediction.
- Do not claim emergency relevance.

## April 2022 X2.2 solar flare sample

- Date: 2022-04-20
- Event type: solar_flare
- Source status: source recorded
- Source note: NASA SVS describes an X2.2 class solar flare on April 20, 2022.
- Source URL: https://svs.gsfc.nasa.gov/4999/

| Candidate page | Baseline before event | Day 0 | Day 1 | Day 2 | Day 7 | Simple delta ratio | Note |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Solar_flare | 0.0 | not available | not available | not available | not available | not available | HTTP 429; retry attempts exhausted |
| Space_weather | 0.0 | not available | not available | not available | not available | not available | HTTP 429; retry attempts exhausted |
| Solar_storm | 0.0 | not available | not available | not available | not available | not available | HTTP 429; retry attempts exhausted |
| Coronal_mass_ejection | 0.0 | not available | not available | not available | not available | not available | HTTP 429; retry attempts exhausted |
| Solar_wind | 0.0 | not available | not available | not available | not available | not available | HTTP 429; retry attempts exhausted |
| Sun | 0.0 | not available | not available | not available | not available | not available | HTTP 429; retry attempts exhausted |
| Space_Weather_Prediction_Center | 0.0 | not available | not available | not available | not available | not available | HTTP 429; retry attempts exhausted |
| Solar_cycle_25 | 310.0 | 448 | 432 | 427 | 273 | 1.45 | daily aggregation only; cache miss |

### Initial Read

- `Solar_cycle_25` ratio 1.45; day 0 448.
- `Solar_flare` ratio not available; day 0 not available.
- `Space_weather` ratio not available; day 0 not available.

### What Not To Claim

- Do not claim awareness.
- Do not claim causality.
- Do not claim prediction.
- Do not claim emergency relevance.

## October 2021 X1.0 solar flare sample

- Date: 2021-10-28
- Event type: solar_flare
- Source status: source recorded
- Source note: NASA image article describes an X1 solar flare on October 28, 2021.
- Source URL: https://www.nasa.gov/image-article/sun-rings-new-month-with-strong-flare/

| Candidate page | Baseline before event | Day 0 | Day 1 | Day 2 | Day 7 | Simple delta ratio | Note |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Solar_flare | 804.14 | 2884 | 6525 | 7643 | 1669 | 9.5 | daily aggregation only; cache miss |
| Space_weather | 112.14 | 111 | 205 | 237 | 142 | 2.11 | daily aggregation only; cache miss |
| Solar_storm | 245.57 | 174 | 275 | 421 | 181 | 1.71 | daily aggregation only; cache miss |
| Coronal_mass_ejection | 466.86 | 1771 | 3818 | 3336 | 1427 | 8.18 | daily aggregation only; cache miss |
| Solar_wind | 542.86 | 592 | 742 | 1228 | 748 | 2.26 | daily aggregation only; cache miss |
| Sun | 5499.43 | 6336 | 6013 | 5447 | 5572 | 1.15 | daily aggregation only; cache miss |
| Space_Weather_Prediction_Center | 10.71 | 30 | 91 | 122 | 45 | 11.39 | daily aggregation only; cache miss |
| Solar_cycle_25 | 175.43 | 389 | 1860 | 1304 | 487 | 10.6 | daily aggregation only; cache miss |

### Initial Read

- `Space_Weather_Prediction_Center` ratio 11.39; day 0 30.
- `Solar_cycle_25` ratio 10.6; day 0 389.
- `Solar_flare` ratio 9.5; day 0 2884.

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
| Solar_flare | 697.0 | 5525 | 6682 | 6999 | 2045 | 10.04 | daily aggregation only; cache miss |
| Space_weather | 0.0 | not available | not available | not available | not available | not available | HTTP 429; retry attempts exhausted |
| Solar_storm | 0.0 | not available | not available | not available | not available | not available | HTTP 429; retry attempts exhausted |
| Coronal_mass_ejection | 472.43 | 3031 | 3477 | 3025 | 830 | 7.36 | daily aggregation only; cache hit |
| Solar_wind | 584.14 | 865 | 944 | 966 | 677 | 1.65 | daily aggregation only; cache hit |
| Sun | 5724.29 | 6487 | 7488 | 6253 | 6336 | 1.31 | daily aggregation only; cache hit |
| Space_Weather_Prediction_Center | 13.29 | 108 | 119 | 72 | 21 | 8.96 | daily aggregation only; cache hit |
| Solar_cycle_24 | 182.0 | 540 | 542 | 666 | 282 | 3.66 | daily aggregation only; cache hit |

### Initial Read

- `Solar_flare` ratio 10.04; day 0 5525.
- `Space_Weather_Prediction_Center` ratio 8.96; day 0 108.
- `Coronal_mass_ejection` ratio 7.36; day 0 3031.

### What Not To Claim

- Do not claim awareness.
- Do not claim causality.
- Do not claim prediction.
- Do not claim emergency relevance.

## September 2017 X8.2 solar flare sample

- Date: 2017-09-10
- Event type: solar_flare
- Source status: source recorded
- Source note: NASA SVS describes the September 10, 2017 X8.2 flare as seen by Solar Dynamics Observatory.
- Source URL: https://svs.gsfc.nasa.gov/4491

| Candidate page | Baseline before event | Day 0 | Day 1 | Day 2 | Day 7 | Simple delta ratio | Note |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Solar_flare | 0.0 | not available | not available | not available | not available | not available | HTTP 429; retry attempts exhausted |
| Space_weather | 0.0 | not available | not available | not available | not available | not available | HTTP 429; retry attempts exhausted |
| Solar_storm | 0.0 | not available | not available | not available | not available | not available | HTTP 429; retry attempts exhausted |
| Coronal_mass_ejection | 0.0 | not available | not available | not available | not available | not available | HTTP 429; retry attempts exhausted |
| Solar_wind | 0.0 | not available | not available | not available | not available | not available | HTTP 429; retry attempts exhausted |
| Sun | 0.0 | not available | not available | not available | not available | not available | HTTP 429; retry attempts exhausted |
| Space_Weather_Prediction_Center | 0.0 | not available | not available | not available | not available | not available | HTTP 429; retry attempts exhausted |
| Solar_cycle_24 | 0.0 | not available | not available | not available | not available | not available | HTTP 429; retry attempts exhausted |

### Initial Read

- `Solar_flare` ratio not available; day 0 not available.
- `Space_weather` ratio not available; day 0 not available.
- `Solar_storm` ratio not available; day 0 not available.

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
| Sun | 0.0 | not available | not available | not available | not available | not available | page not found or no pageview data |
| Space_Weather_Prediction_Center | 0.0 | not available | not available | not available | not available | not available | page not found or no pageview data |
| Carrington_Event | 0.0 | not available | not available | not available | not available | not available | page not found or no pageview data |
| Solar_cycle_24 | 0.0 | not available | not available | not available | not available | not available | page not found or no pageview data |

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
| 2003_Halloween_solar_storms | 0.0 | not available | not available | not available | not available | not available | page not found or no pageview data |
| Solar_flare | 0.0 | not available | not available | not available | not available | not available | page not found or no pageview data |
| Space_weather | 0.0 | not available | not available | not available | not available | not available | page not found or no pageview data |
| Solar_storm | 0.0 | not available | not available | not available | not available | not available | page not found or no pageview data |
| Coronal_mass_ejection | 0.0 | not available | not available | not available | not available | not available | page not found or no pageview data |
| Solar_wind | 0.0 | not available | not available | not available | not available | not available | page not found or no pageview data |
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

