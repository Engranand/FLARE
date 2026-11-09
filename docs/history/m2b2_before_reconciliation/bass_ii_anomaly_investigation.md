# BASS-II anomaly investigation — Milestone 2B-2

Checked 2026-11-05T12:00:46.810348+00:00. **All five anomaly groups remain still unresolved by supporting documentation. None is explained or partially explained by an acquired document.** Observed CSV tokens are verified independently of their scientific meaning.

Source for every cell below: `PSI-25_Experimental table_BASS-II.csv`, SHA-256 `71e792bf6b5fb5ea620c5dd70fbbac05515992e12aefcf5dff47312caa48c042`. Rows are one-based CSV logical/physical rows including header. JSON string notation preserves empty strings, spaces and embedded quotes.

## A. Fan and Air display

Status: **Still unresolved**. Direct source observations:

| Test # | CSV row | Original column | Original value (JSON string) |
| --- | --- | --- | --- |
| B6 | 7 | `Fan display` | `"0.9   1.3   2.75"` |
| B6 | 7 | `Air display` | `"3   5   approaching 10"` |
| M5 | 32 | `Fan display` | `""` |
| M12 | 39 | `Air display` | `"<1"` |
| P5 | 80 | `Fan display` | `"Fan pot 1.5 (5cm/s)   0.9   0.4   0.36   0.32   0.308   0.3   0.29   0.28   0 ext"` |
| P5 | 80 | `Air display` | `"5 down to ext"` |
| O5a | 53 | `Fan display` | `"1.3   2.7   1.3   0.7   0.45. 4.0"` |
| O5a | 53 | `Air display` | `"5  10  5   2   0 (49   62   49   44   42)"` |

Reconciliation finding and remaining uncertainty: Compound strings do not specify a time axis. Empty Fan display is not zero. `<1` is a lexical bound with an unknown unit. P5 contains an explicit local `5cm/s` annotation, but supplies no general display-to-speed calibration. Instrument display versus setpoint versus physical measurement, calibration and missing-value meaning remain unresolved.

## B. Oxygen readings

Status: **Still unresolved**. Direct source observations:

| Test # | CSV row | Original column | Original value (JSON string) |
| --- | --- | --- | --- |
| B2 | 3 | `Calibrated final O2 % by vol` | `"1.6"` |
| P22a | 97 | `Calibrated final O2 % by vol` | `"0.6"` |
| P22b | 98 | `Calibrated final O2 % by vol` | `"39.1"` |
| T28a | 128 | `Calibrated final O2 % by vol` | `"0.9"` |
| T28b | 129 | `Calibrated final O2 % by vol` | `"40.4"` |

Reconciliation finding and remaining uncertainty: Values are transcribed as reported `% by vol`. No supported expected operating range, calibration correction or explanation of the unusual final values was obtained. Do not correct decimals or treat differences as validated depletion or production.

## C. CO and CO2 readings

Status: **Still unresolved**. Direct source observations:

| Test # | CSV row | Original column | Original value (JSON string) |
| --- | --- | --- | --- |
| B4 | 5 | `Initial CO (ppm)` | `"-1"` |
| O5a | 53 | `Initial CO (ppm)` | `"-2"` |
| O20 | 72 | `Initial CO (ppm)` | `"-3"` |
| O4 | 52 | `Final CO (ppm)` | `"OR"` |
| O12 | 62 | `Initial CO (ppm)` | `"OR"` |
| O12 | 62 | `Final CO (ppm)` | `"OR"` |
| O13b | 64 | `Final CO (ppm)` | `"over"` |
| M5 | 32 | `Final CO (ppm)` | `">500"` |
| B2 | 3 | `Final CO2 % by vol` | `""` |
| B2 | 3 | `Final CO (ppm)` | `""` |
| P22a | 97 | `Final CO2 % by vol` | `"none"` |
| P22a | 97 | `Final CO (ppm)` | `"none"` |
| P22b | 98 | `Initial CO2 % by vol` | `"none"` |
| P22b | 98 | `Initial CO (ppm)` | `"none"` |

Reconciliation finding and remaining uncertainty: Negative readings remain negative. OR and over have no verified definition. >500 is not an exact measurement of 500 or proof of a universal instrument maximum: P5 Final CO is 525 (row 80), and O13b Initial CO is 950 (row 64). Empty and literal none remain distinct; neither is measured zero. Detection limits, instrument range, offsets and reasons for missing gas readings remain unknown.

## D. GMT and dates

Status: **Still unresolved**. Direct source observations:

| Test # | CSV row | Original column | Original value (JSON string) |
| --- | --- | --- | --- |
| B1 | 2 | `Date` | `"2/19/2014"` |
| B1 | 2 | `GMT` | `"50"` |
| O20 | 72 | `Date` | `"2/26/2016"` |
| O20 | 72 | `GMT` | `"57"` |
| O21 | 73 | `Date` | `"2/26/2016"` |
| O21 | 73 | `GMT` | `"57"` |
| O22 | 74 | `Date` | `"2/26/2016"` |
| O22 | 74 | `GMT` | `"57"` |
| T9 | 109 | `Date` | `"6/24/2018"` |
| T9 | 109 | `GMT` | `"175"` |
| T18 | 118 | `Date` | `"6/24/2018"` |
| T18 | 118 | `GMT` | `"175"` |

Reconciliation finding and remaining uncertainty: Date strings are slash-form; 124 end in 2014, three in 2016 and two in 2018. GMT is numeric-looking text, not an established timestamp or day-of-year. Event timing, time basis and whether unusual years are errors remain unresolved; no date correction is warranted.

## E. Radiometer gain

Status: **Still unresolved**. Direct source observations:

| Test # | CSV row | Original column | Original value (JSON string) |
| --- | --- | --- | --- |
| B1 | 2 | `Radiometer gain   (1000   250   50   10)` | `"50"` |
| M12 | 39 | `Radiometer gain   (1000   250   50   10)` | `"250>50"` |
| P5 | 80 | `Radiometer gain   (1000   250   50   10)` | `"250>50"` |

Reconciliation finding and remaining uncertainty: The header labels gain and lists 1000, 250, 50, 10; cells also contain transitions such as 250>50. This lexical evidence does not establish hardware response, calibration, transition timing or radiant-flux units. Do not interpret these as calibrated radiation measurements.

## Missingness and comparison limitations
There are 19 empty strings and 16 literal `none` cells. These counts describe source tokens, not a documented missing-value codebook. The parser reports 13 negative_numeric cells and 4 ambiguous_token cells across the file; its classifications are lexical, not scientific diagnoses. Preserve them all. Repeated samples, compound settings, incomplete fuel descriptions and unknown per-test flow direction prevent automatic comparability claims.

## Supporting-document evidence and next action
The [ReadMe](source_extracts/bass_ii_readme_extracted.md) and [workbook](source_extracts/bass_ii_test_matrices_inspection.md) acquisition notes contain the failed attempts and manual action. No paper statement or investigation description has been substituted for a per-record measurement or document definition. Resolve these questions from acquired originals with paragraph/sheet/cell references before semantic ingestion or analysis.
