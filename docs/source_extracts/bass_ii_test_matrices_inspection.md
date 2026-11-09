# BASS-II Test Matrices structural inspection — M2B-2R

Sources throughout: CSV = `PSI-25_Experimental table_BASS-II.csv`; FAQ = `BASS-II data FAQ.docx`; workbook = `BASS-II Test Matrix by PI Final.xlsx`. These shorthand names always refer to the immutable files in `data/raw/bass_ii/original/`, with hashes in the [manifest](../../data/manifests/bass_ii_acquisition_manifest.json). CSV rows include the header (B1 is row 2). Worksheet references preserve actual names, including `T'ien`.

FAQ page references use the file's saved Word pagination, not a new render: six `lastRenderedPageBreak` markers agree with seven pages in document properties. Exact paragraph IDs and complete text are in the [extraction](bass_ii_readme_extracted.md). Fresh rendering was unavailable because LibreOffice was not installed. The user-supplied filenames and expected portal aliases are recorded separately; hash agreement is with user-provided baselines, not an independently published NASA checksum.

Both ZIP CRC and every OOXML XML member parsed successfully. Read-only openpyxl loading also succeeded. No workbook save, recalculation or formula evaluation was performed.

| Worksheet | Visibility | Used range | Test rows | Empty cells in range | Merged cells | Formulas | Comments |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `Bhattacharjee` | visible | A1:P23 | 22 | 2 | none | 0 | 0 |
| `Ferkul` | visible | A1:P5 | 4 | 0 | none | 0 | 0 |
| `Miller` | visible | A1:P21 | 20 | 1 | none | 0 | 0 |
| `Olson` | visible | A1:P28 | 27 | 6 | none | 0 | 0 |
| `Fernandez-Pello` | visible | A1:P28 | 27 | 4 | none | 0 | 0 |
| `T'ien` | visible | A1:P30 | 29 | 6 | none | 0 | 0 |

All six sheets are visible; no hidden rows or columns were found. Each has one header row and a contiguous 16-column table. There are 129 test rows and 19 empty cells total. No formula cells exist, so no formula cached results exist to validate; ordinary `<v>` numeric/string values are not formula caches. No cell comments or hyperlinks were found. In-cell annotations (for example Ferkul G5 `see notes`) remain ordinary source text, not separately verified notes. No fan-calibration worksheet is present despite the FAQ's reference to calibration information in a folder (FAQ p. 1, paragraph 1).

## Original headers

The following headers occur at the same coordinates on all six sheets except Olson B1, shown separately. Whitespace is retained using JSON strings. `PI` is not a workbook column: exact worksheet name supplies that association (FAQ p. 1, paragraphs 4–10).

| Cell on every sheet | Original header |
| --- | --- |
| A1 | `"Actual Date  (for Video Display Date, add 1 for Leap Year)"` |
| B1 | `"GMT 2014-"` |
| C1 | `"Test no."` |
| D1 | `"Sample no."` |
| E1 | `"Material"` |
| F1 | `"Flow restrictor"` |
| G1 | `"Fan display"` |
| H1 | `"Air display"` |
| I1 | `"Radiometer gain   (1000, 250, 50, 10)"` |
| J1 | `"total frames shot"` |
| K1 | `"calibrated  initial O2 % by vol "` |
| L1 | `"calibrated final O2 % by vol"` |
| M1 | `"Initial CO2 % by vol"` |
| N1 | `"Final CO2 % by vol"` |
| O1 | `"Initial CO (ppm)"` |
| P1 | `"Final CO (ppm)"` |

Olson B1: `"GMT 2014- (except last 3 tests from 2016)"`.

## Cell types and evidence preservation

[Workbook evidence JSON](bass_ii_workbook_evidence.json) enumerates every cell in each used range, including empty cells, with sheet name, coordinate, decoded value/type, Excel number format, raw XML type/value lexeme and formula (null here). Numeric Excel date serials remain in `xml_value`; `value` additionally shows the library-decoded ISO date. The midnight component represents the date serialization, not an experiment time. CSV slash-date strings are retained separately in every record mapping. For string cells, raw `xml_value` may be a shared-string index; the decoded original string is in `value`. Absent cells and stored empty cells have null content; the original XML package remains authoritative for storage details.

All test identifiers are in column C; sample identifiers in D; material E; restrictor F; fan G; air H; radiometer I; frames J; initial/final O2 K/L; CO2 M/N; CO O/P. Date is A and GMT is B. The [mapping](../bass_ii_test_matrix_mapping.md) lists all 129 exact joins, repeated samples and both representations of all 516 presentation-sensitive cells. No identifier suffix was stripped and no fuzzy match was used.
