# BASS-II field reconciliation — Milestone 2B-2

Checked 2026-11-05T12:00:46.810348+00:00. Supporting documents could not be acquired; **0 confirmed, 0 partially_confirmed, 17 unresolved, 0 not_applicable**. Here status concerns corroboration by the requested DOCX/XLSX. CSV labels and units remain directly observable, but do not establish calibration, operational definitions or validity.

Evidence CSV: `PSI-25_Experimental table_BASS-II.csv`, SHA-256 `71e792bf6b5fb5ea620c5dd70fbbac05515992e12aefcf5dff47312caa48c042`. CSV row 1 is the header; data starts at row 2. All records are single physical lines. Exact headers below use code spans; spaces inside them are significant.

| CSV field | ReadMe definition | Test Matrices mapping | Units | Interpretation status | Evidence reference |
| --- | --- | --- | --- | --- | --- |
| `PI` | Unavailable; not inspected | Unavailable; not inspected | Not stated | unresolved | CSV header row 1, column 1; B1 row 2, `PI`; supporting-document failure notes below |
| `Test #` | Unavailable; not inspected | Unavailable; not inspected | Not stated | unresolved | CSV header row 1, column 2; B1 row 2, `Test #`; supporting-document failure notes below |
| `Date` | Unavailable; not inspected | Unavailable; not inspected | Not stated; slash-form date text | unresolved | CSV header row 1, column 3; B1 row 2, `Date`; supporting-document failure notes below |
| `GMT` | Unavailable; not inspected | Unavailable; not inspected | Not stated | unresolved | CSV header row 1, column 4; B1 row 2, `GMT`; supporting-document failure notes below |
| `Sample #` | Unavailable; not inspected | Unavailable; not inspected | Not stated | unresolved | CSV header row 1, column 5; B1 row 2, `Sample #`; supporting-document failure notes below |
| `Fuel Sample Material` | Unavailable; not inspected | Unavailable; not inspected | Units embedded in descriptions; no universal unit | unresolved | CSV header row 1, column 6; B1 row 2, `Fuel Sample Material`; supporting-document failure notes below |
| `Flow restrictor` | Unavailable; not inspected | Unavailable; not inspected | Not stated | unresolved | CSV header row 1, column 7; B1 row 2, `Flow restrictor`; supporting-document failure notes below |
| `Fan display` | Unavailable; not inspected | Unavailable; not inspected | Not stated globally; P5 explicitly contains 5cm/s | unresolved | CSV header row 1, column 8; B1 row 2, `Fan display`; supporting-document failure notes below |
| `Air display` | Unavailable; not inspected | Unavailable; not inspected | Not stated | unresolved | CSV header row 1, column 9; B1 row 2, `Air display`; supporting-document failure notes below |
| `Radiometer gain   (1000   250   50   10)` | Unavailable; not inspected | Unavailable; not inspected | Not stated; header lists settings | unresolved | CSV header row 1, column 10; B1 row 2, `Radiometer gain   (1000   250   50   10)`; supporting-document failure notes below |
| `Total Frames Shot` | Unavailable; not inspected | Unavailable; not inspected | Frames suggested by header; capture semantics unverified | unresolved | CSV header row 1, column 11; B1 row 2, `Total Frames Shot`; supporting-document failure notes below |
| `Calibrated  initial O2 % by vol ` | Unavailable; not inspected | Unavailable; not inspected | % by vol (header) | unresolved | CSV header row 1, column 12; B1 row 2, `Calibrated  initial O2 % by vol `; supporting-document failure notes below |
| `Calibrated final O2 % by vol` | Unavailable; not inspected | Unavailable; not inspected | % by vol (header) | unresolved | CSV header row 1, column 13; B1 row 2, `Calibrated final O2 % by vol`; supporting-document failure notes below |
| `Initial CO2 % by vol` | Unavailable; not inspected | Unavailable; not inspected | % by vol (header) | unresolved | CSV header row 1, column 14; B1 row 2, `Initial CO2 % by vol`; supporting-document failure notes below |
| `Final CO2 % by vol` | Unavailable; not inspected | Unavailable; not inspected | % by vol (header) | unresolved | CSV header row 1, column 15; B1 row 2, `Final CO2 % by vol`; supporting-document failure notes below |
| `Initial CO (ppm)` | Unavailable; not inspected | Unavailable; not inspected | ppm (header; basis unspecified) | unresolved | CSV header row 1, column 16; B1 row 2, `Initial CO (ppm)`; supporting-document failure notes below |
| `Final CO (ppm)` | Unavailable; not inspected | Unavailable; not inspected | ppm (header; basis unspecified) | unresolved | CSV header row 1, column 17; B1 row 2, `Final CO (ppm)`; supporting-document failure notes below |

## Evidence and identity limitations
[ReadMe acquisition evidence](source_extracts/bass_ii_readme_extracted.md) and [Test Matrices acquisition evidence](source_extracts/bass_ii_test_matrices_inspection.md) explain why no scientific definition is attributed to either document. All 17 entries explicitly remain unresolved.

Test IDs P22a/P22b occur at CSV rows 97–98 with Sample # `200m`; T28a/T28b occur at rows 128–129 with Sample # `144m`. These are distinct source rows, not proven independent physical experiments. Preserve suffixes and case. The workbook may describe planned configurations rather than performed runs; that possibility is an engineering caution, not a source finding.

## Engineering decisions
Keep existing lexical classification and raw strings unchanged. Units explicitly in gas headers remain available as source labels; no new canonical units, conversion factors, calibration equations, timestamp interpretations or instrument definitions are introduced. Acquisition failure does not justify treating any field as not_applicable.
