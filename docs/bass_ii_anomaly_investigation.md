# BASS-II anomaly investigation — M2B-2R

Sources throughout: CSV = `PSI-25_Experimental table_BASS-II.csv`; FAQ = `BASS-II data FAQ.docx`; workbook = `BASS-II Test Matrix by PI Final.xlsx`. These shorthand names always refer to the immutable files in `data/raw/bass_ii/original/`, with hashes in the [manifest](../data/manifests/bass_ii_acquisition_manifest.json). CSV rows include the header (B1 is row 2). Worksheet references preserve actual names, including `T'ien`.

FAQ page references use the file's saved Word pagination, not a new render: six `lastRenderedPageBreak` markers agree with seven pages in document properties. Exact paragraph IDs and complete text are in the [extraction](source_extracts/bass_ii_readme_extracted.md). Fresh rendering was unavailable because LibreOffice was not installed. The user-supplied filenames and expected portal aliases are recorded separately; hash agreement is with user-provided baselines, not an independently published NASA checksum.

## Negative CO — still unresolved

All **13 negative CO values occur in Initial CO (ppm)**. Every one agrees with workbook column O. FAQ p. 2 paragraph 25 identifies CSA-CP and defines OR, but does not explain instrument zero offsets, calibration error, background subtraction or why these readings are negative. None of those mechanisms is asserted here. No clamping, subtraction or missing-value substitution is justified.

| Test | CSV row | CSV field | CSV raw | Workbook sheet!cell | Workbook original |
| --- | --- | --- | --- | --- | --- |
| B4 | 5 | `Initial CO (ppm)` | `"-1"` | `Bhattacharjee!O5` | `-1` |
| B21 | 22 | `Initial CO (ppm)` | `"-1"` | `Bhattacharjee!O22` | `-1` |
| B22 | 23 | `Initial CO (ppm)` | `"-1"` | `Bhattacharjee!O23` | `-1` |
| M10 | 37 | `Initial CO (ppm)` | `"-1"` | `Miller!O11` | `-1` |
| O1 | 48 | `Initial CO (ppm)` | `"-1"` | `Olson!O2` | `-1` |
| O2 | 49 | `Initial CO (ppm)` | `"-1"` | `Olson!O3` | `-1` |
| O5a | 53 | `Initial CO (ppm)` | `"-2"` | `Olson!O7` | `-2` |
| O20 | 72 | `Initial CO (ppm)` | `"-3"` | `Olson!O26` | `-3` |
| T25 | 125 | `Initial CO (ppm)` | `"-1"` | `T'ien!O25` | `-1` |
| T26 | 126 | `Initial CO (ppm)` | `"-1"` | `T'ien!O26` | `-1` |
| T27 | 127 | `Initial CO (ppm)` | `"-1"` | `T'ien!O27` | `-1` |
| T28a | 128 | `Initial CO (ppm)` | `"-1"` | `T'ien!O28` | `-1` |
| T29 | 130 | `Initial CO (ppm)` | `"-1"` | `T'ien!O30` | `-1` |

## CO over-range — OR explained; over still unresolved

FAQ p. 2 paragraph 25 states `OR = over range (> 1000 ppm)`. This supports a semantic lower-bound interpretation for OR, not a point value. The literal `over` has no separate definition anywhere in the inspected FAQ or workbook. Its probable similarity is not sufficient evidence to assign the same limit. `>500` already supplies its own bound; it is not a documented global sensor limit. No value is replaced with 500, 1000 or 1001. Parser labels remain unchanged.

| Test | CSV row | CSV field | CSV raw | Workbook sheet!cell | Workbook original |
| --- | --- | --- | --- | --- | --- |
| O4 | 52 | `Final CO (ppm)` | `"OR"` | `Olson!P6` | `"OR"` |
| O12 | 62 | `Initial CO (ppm)` | `"OR"` | `Olson!O16` | `"OR"` |
| O12 | 62 | `Final CO (ppm)` | `"OR"` | `Olson!P16` | `"OR"` |
| O13b | 64 | `Final CO (ppm)` | `"over"` | `Olson!P18` | `"over"` |
| M5 | 32 | `Final CO (ppm)` | `">500"` | `Miller!P6` | `">500"` |
| P5 | 80 | `Final CO (ppm)` | `"525"` | `Fernandez-Pello!P7` | `525` |
| O13b | 64 | `Initial CO (ppm)` | `"950"` | `Olson!O18` | `950` |

## Unusual final oxygen — calibration context partially explained; individual readings unresolved

FAQ p. 2 paragraph 23 documents an out-of-calibration O2 sensor and a daily constant-offset correction using the MCA initial ISS air reading. It supplies neither the daily offsets nor uncertainty and does not explain the following readings. All five appear unchanged in workbook column L, so these are not demonstrated CSV transcription errors. Preserve them without correction, interpolation, a second calibration, or interpreting their differences as validated oxygen consumption.

| Test | CSV row | CSV field | CSV raw | Workbook sheet!cell | Workbook original |
| --- | --- | --- | --- | --- | --- |
| B2 | 3 | `Calibrated final O2 % by vol` | `"1.6"` | `Bhattacharjee!L3` | `1.6` |
| P22a | 97 | `Calibrated final O2 % by vol` | `"0.6"` | `Fernandez-Pello!L24` | `0.6` |
| P22b | 98 | `Calibrated final O2 % by vol` | `"39.1"` | `Fernandez-Pello!L25` | `39.1` |
| T28a | 128 | `Calibrated final O2 % by vol` | `"0.9"` | `T'ien!L28` | `0.9` |
| T28b | 129 | `Calibrated final O2 % by vol` | `"40.4"` | `T'ien!L29` | `40.4` |

## Dates and GMT — 2016 supported; 2018 remains contradictory

FAQ p. 1 paragraphs 13–14 defines Date as actual experiment date and GMT as day of year. Its one-day video-display offset concerns the onboard video's date, not an instruction to shift the matrix's Actual Date. All worksheet A1 headers explicitly say to add 1 for Video Display Date. Do not use this explanation to change years.

Olson B1 says `GMT 2014- (except last 3 tests from 2016)`; Olson A26:A28, B26:B28 and C26:C28 corroborate O20–O22 on 2016-02-26, day 57. The three 2016 entries are therefore supported by the workbook's explicit exception. T'ien B1 instead says `GMT 2014-`, while A9 and A18 store 2018-06-24 (tests T9/T18) and B9/B18 store 175. The CSV agrees with those cell dates. No exception explains that conflict, so 2018 is retained and the intended year remains unresolved. A day-of-year match alone cannot decide the year. No full timestamp or time of day was derived.

| Test | CSV row | CSV field | CSV raw | Workbook sheet!cell | Workbook original |
| --- | --- | --- | --- | --- | --- |
| O20 | 72 | `Date` | `"2/26/2016"` | `Olson!A26` | `"2016-02-26T00:00:00"` |
| O20 | 72 | `GMT` | `"57"` | `Olson!B26` | `57` |
| O21 | 73 | `Date` | `"2/26/2016"` | `Olson!A27` | `"2016-02-26T00:00:00"` |
| O21 | 73 | `GMT` | `"57"` | `Olson!B27` | `57` |
| O22 | 74 | `Date` | `"2/26/2016"` | `Olson!A28` | `"2016-02-26T00:00:00"` |
| O22 | 74 | `GMT` | `"57"` | `Olson!B28` | `57` |
| T9 | 109 | `Date` | `"6/24/2018"` | `T'ien!A9` | `"2018-06-24T00:00:00"` |
| T9 | 109 | `GMT` | `"175"` | `T'ien!B9` | `175` |
| T18 | 118 | `Date` | `"6/24/2018"` | `T'ien!A18` | `"2018-06-24T00:00:00"` |
| T18 | 118 | `GMT` | `"175"` | `T'ien!B18` | `175` |

## Fan, air and restrictor — definitions explained; mixed records partially explained

FAQ p. 1 paragraphs 18–20 distinguishes inlet perforated plates, instantaneous video fan voltage ×10 (122 = 12.2 V), control-box pot settings (maximum 10), and duct air velocity in cm/s. The air display responds in about one minute and is steady only after long periods at an unchanged setting. A number such as 10 cannot be assumed to be voltage, pot position or airflow without its cell context. No fan-to-flow calibration curve is included in these two documents; the FAQ merely mentions a calibration-information folder (p. 1 paragraph 1). No conversions were performed.

The `<1` Air display entry is now associated with a cm/s-labeled measurement definition, but the actual settling/validity of that reading is not documented. Compound settings retain their sequence text without an invented time axis. Missing fan/air values remain unknown rather than zero. Annotations inside Air display can also mention pot values and must not all inherit cm/s.

| Test | CSV row | CSV field | CSV raw | Workbook sheet!cell | Workbook original |
| --- | --- | --- | --- | --- | --- |
| B6 | 7 | `Fan display` | `"0.9   1.3   2.75"` | `Bhattacharjee!G7` | `"0.9, 1.3, 2.75"` |
| B6 | 7 | `Air display` | `"3   5   approaching 10"` | `Bhattacharjee!H7` | `"3, 5, approaching 10"` |
| M5 | 32 | `Fan display` | `""` | `Miller!G6` | `null` |
| M12 | 39 | `Air display` | `"<1"` | `Miller!H13` | `"<1"` |
| P5 | 80 | `Fan display` | `"Fan pot 1.5 (5cm/s)   0.9   0.4   0.36   0.32   0.308   0.3   0.29   0.28   0 ext"` | `Fernandez-Pello!G7` | `"Fan pot 1.5 (5cm/s), 0.9, 0.4, 0.36, 0.32, 0.308, 0.3, 0.29, 0.28, 0 ext"` |
| P5 | 80 | `Air display` | `"5 down to ext"` | `Fernandez-Pello!H7` | `"5 down to ext"` |
| P2 | 76 | `Air display` | `"5   2.5   2 (pot .9   .5   .35.  .33)"` | `Fernandez-Pello!H3` | `"5, 2.5, 2 (pot .9, .5, .35.,.33)"` |
| O5a | 53 | `Fan display` | `"1.3   2.7   1.3   0.7   0.45. 4.0"` | `Olson!G7` | `"1.3, 2.7, 1.3, 0.7, 0.45. 4.0"` |

## Radiometer — uncalibrated setting explained; absolute intensity unavailable

FAQ p. 2 paragraph 21 explicitly calls the gain uncalibrated and says it was adjusted to avoid saturation. It discusses relative flame intensity/dynamics and a 5 Hz video display rate. That rate is not a Nikon still-frame rate and does not create a timestamp series from the CSV. Column I contains gain settings, not measured radiometer intensities. Neither scalar gain nor transitions support absolute flame intensity or cross-gain normalization without further evidence.

| Test | CSV row | CSV field | CSV raw | Workbook sheet!cell | Workbook original |
| --- | --- | --- | --- | --- | --- |
| B1 | 2 | `Radiometer gain   (1000   250   50   10)` | `"50"` | `Bhattacharjee!I2` | `50` |
| M12 | 39 | `Radiometer gain   (1000   250   50   10)` | `"250>50"` | `Miller!I13` | `"250>50"` |
| P5 | 80 | `Radiometer gain   (1000   250   50   10)` | `"250>50"` | `Fernandez-Pello!I7` | `"250>50"` |
| O3b | 51 | `Radiometer gain   (1000   250   50   10)` | `"1000   250"` | `Olson!I5` | `"1000, 250"` |

## Missingness — reasons still unresolved

There are 19 empty cells and 16 literal `none` cells; workbook and CSV agree at every corresponding location. The FAQ provides no general missing-value codebook. Neither blank nor none becomes zero, OR or an instrument failure. The table below lists every missing marker with source coordinates; a recorded numeric zero remains separate.

| Test | CSV row | CSV field | CSV raw | Workbook sheet!cell | Workbook original |
| --- | --- | --- | --- | --- | --- |
| B2 | 3 | `Total Frames Shot` | `"none"` | `Bhattacharjee!J3` | `"none"` |
| B2 | 3 | `Final CO2 % by vol` | `""` | `Bhattacharjee!N3` | `null` |
| B2 | 3 | `Final CO (ppm)` | `""` | `Bhattacharjee!P3` | `null` |
| B14 | 15 | `Calibrated final O2 % by vol` | `"none"` | `Bhattacharjee!L15` | `"none"` |
| B14 | 15 | `Final CO2 % by vol` | `"none"` | `Bhattacharjee!N15` | `"none"` |
| B14 | 15 | `Final CO (ppm)` | `"none"` | `Bhattacharjee!P15` | `"none"` |
| F3 | 26 | `Calibrated final O2 % by vol` | `"none"` | `Ferkul!L4` | `"none"` |
| F3 | 26 | `Final CO2 % by vol` | `"none"` | `Ferkul!N4` | `"none"` |
| F3 | 26 | `Final CO (ppm)` | `"none"` | `Ferkul!P4` | `"none"` |
| M5 | 32 | `Fan display` | `""` | `Miller!G6` | `null` |
| O3a | 50 | `Fan display` | `""` | `Olson!G4` | `null` |
| O3b | 51 | `Fan display` | `""` | `Olson!G5` | `null` |
| O7 | 56 | `Air display` | `""` | `Olson!H10` | `null` |
| O8a | 57 | `Air display` | `""` | `Olson!H11` | `null` |
| O8b | 58 | `Air display` | `""` | `Olson!H12` | `null` |
| O9 | 59 | `Air display` | `""` | `Olson!H13` | `null` |
| P1 | 75 | `Fan display` | `""` | `Fernandez-Pello!G2` | `null` |
| P2 | 76 | `Fan display` | `""` | `Fernandez-Pello!G3` | `null` |
| P3a | 77 | `Fan display` | `""` | `Fernandez-Pello!G4` | `null` |
| P3b | 78 | `Fan display` | `""` | `Fernandez-Pello!G5` | `null` |
| P3b | 78 | `Final CO2 % by vol` | `"none"` | `Fernandez-Pello!N5` | `"none"` |
| P22a | 97 | `Final CO2 % by vol` | `"none"` | `Fernandez-Pello!N24` | `"none"` |
| P22a | 97 | `Final CO (ppm)` | `"none"` | `Fernandez-Pello!P24` | `"none"` |
| P22b | 98 | `Initial CO2 % by vol` | `"none"` | `Fernandez-Pello!M25` | `"none"` |
| P22b | 98 | `Initial CO (ppm)` | `"none"` | `Fernandez-Pello!O25` | `"none"` |
| T6 | 107 | `Fan display` | `""` | `T'ien!G7` | `null` |
| T13 | 113 | `Fan display` | `""` | `T'ien!G13` | `null` |
| T14 | 114 | `Fan display` | `""` | `T'ien!G14` | `null` |
| T16 | 116 | `Fan display` | `""` | `T'ien!G16` | `null` |
| T17 | 117 | `Fan display` | `""` | `T'ien!G17` | `null` |
| T18 | 118 | `Fan display` | `""` | `T'ien!G18` | `null` |
| T28a | 128 | `Final CO2 % by vol` | `"none"` | `T'ien!N28` | `"none"` |
| T28a | 128 | `Final CO (ppm)` | `"none"` | `T'ien!P28` | `"none"` |
| T28b | 129 | `Initial CO2 % by vol` | `"none"` | `T'ien!M29` | `"none"` |
| T28b | 129 | `Initial CO (ppm)` | `"none"` | `T'ien!O29` | `"none"` |

## Scope of conclusions

Documented: field meanings, OR threshold, the 2016 year exception, video-date offset context, uncalibrated gain and air-response limitation. Partially established: O2 calibration procedure and applicability of mixed fan/air settings. Unresolved: negative CO causes, independent meaning of over, anomalous O2 readings, intended T9/T18 years, daily calibration coefficients, missing-value reasons, sample m/M suffix meaning, sensor uncertainty and comparable steady conditions. No paper's bibliographic entry was used as experimental data. All prior acquisition-failure findings remain available in [history](history/m2b2_before_reconciliation/bass_ii_anomaly_investigation.md).
