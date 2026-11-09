# BASS-II original source reconciliation

Milestone 2B-0: **Both available CSV copies verified locally. ReadMe DOCX and Test Matrices XLSX pending acquisition.**

Verification timestamp: `2026-11-05T11:30:00.368342+00:00` (UTC). The user clarified that only the CSV files have been downloaded. The DOCX and XLSX have not been downloaded; their content is not reconstructed or inferred. The originally specified `data/raw/bass_ii/original/` directory does not exist in this checkout. Both CSVs were found and inspected read-only in `C:\Users\anand\Downloads`, without copying, moving or renaming them.

## Acquisition and preservation

| Actual filename | Actual size (bytes) | Detected format | Status |
| --- | ---: | --- | --- |
| PSI-25_Experimental table_BASS-II.csv | 16590 | UTF-8 BOM, comma-delimited CSV text | Verified local bytes |
| PSI-25_Experimental table_BASS-II (1).csv | 16590 | Same | Verified local bytes; byte-identical copy |
| ReadMe DOCX — no local filename | Unknown | Not inspected | Pending acquisition, confirmed by user |
| Test Matrices XLSX — no local filename | Unknown | Not inspected | Pending acquisition, confirmed by user |

Both CSVs have SHA-256:

```text
71e792bf6b5fb5ea620c5dd70fbbac05515992e12aefcf5dff47312caa48c042
```

Hashes were recomputed after inspection and were unchanged. Both full byte arrays also compared equal. This is a duplicate file download, not duplicate experimental rows. No file was classified as corrupt; the CSV parses strictly, while the missing documents cannot be tested for corruption/readability.

Expected NASA document filenames, from the user and prior audit:

- `PSI-25_Science Documents_BASS-II_ReadMe.docx`
- `PSI-25_Science Documents_BASS-II_Test.Matrices.xlsx`

Source identity: PSI-25, Burning and Suppression of Solids-II (BASS-II), DOI `10.60555/4qc4-de67`, [NASA landing page](https://psi.nasa.gov/physci/repo/data/investigations/PSI-25). This association relies on the user's manual-download account, matching primary filename and the prior source audit. No NASA-published checksum was compared. The prior browser audit examined Version 4; the downloaded CSV alone does not establish its source version. Download timestamps are unknown. File modification timestamps are not treated as acquisition timestamps.

The [JSON manifest](../data/manifests/bass_ii_acquisition_manifest.json) records both actual paths/hashes, exact headers, missing-cell locations, unusual gas values, reconciliation results and post-inspection hash checks. Its previous missing-all-files status is superseded by this partial verification; this is not completion of all three-file verification.

## CSV byte structure

- BOM: bytes `EF BB BF`; strict UTF-8 decoding succeeded after the BOM. Encoding: UTF-8 with BOM.
- Delimiter: comma. Quote character: double quote. Embedded quotes use doubled double quotes. No backslash escape was needed. Inspection used strict standard-library CSV decoding with initial whitespace preserved.
- Quoting evidence: physical line 48 (O1) contains the source field `"1/4"" clear rod"`, which decodes to `1/4" clear rod`. Structural CSV quotes must not become measurement text.
- Newlines: 130 CRLF sequences, no lone CR or LF. The file ends in CRLF.
- **130 logical records including one header; 129 data records; zero blank logical records.** All 130 records have 17 fields. No multiline records were found. Physical line = logical record number for this file.
- Physical line 1 is the header; B1 is line 2 and T29 is line 130. A terminal CRLF terminates the last record; it does not create another blank CSV record.
- No duplicate nonempty Test # values, missing Test # values, or exact duplicate complete data rows were found. Sample reuse and a/b test suffixes remain separate from duplicate detection.

### Exact original headers

JSON string notation below makes leading/trailing spaces visible inside quotes. Header 12 contains two spaces after `Calibrated` and one trailing space. Header 10 contains repeated internal spaces. These strings were extracted from the file; no header normalization was applied to the originals.

1. `"PI"`
2. `"Test #"`
3. `"Date"`
4. `"GMT"`
5. `"Sample #"`
6. `"Fuel Sample Material"`
7. `"Flow restrictor"`
8. `"Fan display"`
9. `"Air display"`
10. `"Radiometer gain   (1000   250   50   10)"`
11. `"Total Frames Shot"`
12. `"Calibrated  initial O2 % by vol "`
13. `"Calibrated final O2 % by vol"`
14. `"Initial CO2 % by vol"`
15. `"Final CO2 % by vol"`
16. `"Initial CO (ppm)"`
17. `"Final CO (ppm)"`

### B1–B10 reconciliation

All 17 fields per record were compared against the three record tables in [Milestone 2A source audit](bass_ii_source_audit.md), including PI, identifiers, date, sample/material, settings, frame count and all six gas readings. The report's blank marker was mapped to an empty string **for comparison only**, and whitespace was collapsed on both sides because the prior report explicitly normalized display whitespace. **170/170 field values match under that comparison; no numerical, identifier, missing-marker or non-whitespace textual mismatch was found.** This is not byte-for-byte equality with the prior Markdown.

| Test ID | Original physical line / logical record | Comparison | Fields with whitespace-only differences |
| --- | ---: | --- | ---: |
| B1 | 2 | 17/17 match after display-whitespace normalization | 1 |
| B2 | 3 | 17/17 match after display-whitespace normalization | 1 |
| B3 | 4 | 17/17 match after display-whitespace normalization | 1 |
| B4 | 5 | 17/17 match after display-whitespace normalization | 1 |
| B5 | 6 | 17/17 match after display-whitespace normalization | 1 |
| B6 | 7 | 17/17 match after display-whitespace normalization | 2 |
| B7 | 8 | 17/17 match after display-whitespace normalization | 1 |
| B8 | 9 | 17/17 match after display-whitespace normalization | 3 |
| B9 | 10 | 17/17 match after display-whitespace normalization | 3 |
| B10 | 11 | 17/17 match after display-whitespace normalization | 3 |

Raw differences retained in the manifest include triple spaces in material/setting cells and trailing spaces in B4/B5 material descriptions. B2 line 3 retains frame count `none`, final CO2 blank and final CO blank. B4 line 5 retains initial CO `-1`. B6 line 7 retains final CO `0.3`. B8 line 9 retains restrictor `0` and the full display qualifiers. B9 line 10 retains `<1`. B10 line 11 retains the complete multi-value settings; no times or averages are invented.

### Missing and unusual values

Counts across 129 data records match the prior audit's counts excluding its displayed blank row:

| Original column (display whitespace collapsed) | Empty strings | Literal `none` |
| --- | ---: | ---: |
| Fan display | 13 | 0 |
| Air display | 4 | 0 |
| Total Frames Shot | 0 | 1 |
| Calibrated final O2 % by vol | 0 | 2 |
| Initial CO2 % by vol | 0 | 2 |
| Final CO2 % by vol | 1 | 5 |
| Initial CO (ppm) | 0 | 2 |
| Final CO (ppm) | 1 | 4 |

Other columns contain no empty strings or literal `none` tokens. Empty strings, `none`, numeric `0`, negative readings and ambiguous tokens remain distinct. Complete missing-cell locators are in the manifest. Numeric-looking gas values were checked lexically; the following negative or nonnumeric non-missing values were found:

| Test ID | Physical line | Original column | Original value |
| --- | ---: | --- | --- |
| B4 | 5 | Initial CO (ppm) | `-1` |
| B21 | 22 | Initial CO (ppm) | `-1` |
| B22 | 23 | Initial CO (ppm) | `-1` |
| M5 | 32 | Final CO (ppm) | `>500` |
| M10 | 37 | Initial CO (ppm) | `-1` |
| O1 | 48 | Initial CO (ppm) | `-1` |
| O2 | 49 | Initial CO (ppm) | `-1` |
| O4 | 52 | Final CO (ppm) | `OR` |
| O5a | 53 | Initial CO (ppm) | `-2` |
| O12 | 62 | Initial CO (ppm) | `OR` |
| O12 | 62 | Final CO (ppm) | `OR` |
| O13b | 64 | Final CO (ppm) | `over` |
| O20 | 72 | Initial CO (ppm) | `-3` |
| T25 | 125 | Initial CO (ppm) | `-1` |
| T26 | 126 | Initial CO (ppm) | `-1` |
| T27 | 127 | Initial CO (ppm) | `-1` |
| T28a | 128 | Initial CO (ppm) | `-1` |
| T29 | 130 | Initial CO (ppm) | `-1` |

`>500` is not an exact reading of 500. `OR` and `over` have no verified definition yet. Negative values include -1, -2 and -3; they are preserved, not clamped or reclassified as missing. Settings also contain sequences, `pot`, `max`, `approaching`, `ext`, inequalities, transitions and question marks. Their meanings/units remain unresolved without documentation.

Unusual final O2 entries from the audit are confirmed in the CSV: B2 line 3 = 1.6; P22a line 97 = 0.6; P22b line 98 = 39.1; T28a line 128 = 0.9; T28b line 129 = 40.4, all under the original `% by vol` header. No physical interpretation or correction is made.

The Date column has 124 entries ending in 2014, three in 2016 and two in 2018. All non-2014 entries are listed below for review, without asserting they are errors:

| Test ID | Physical line | Original Date |
| --- | ---: | --- |
| O20 | 72 | 2/26/2016 |
| O21 | 73 | 2/26/2016 |
| O22 | 74 | 2/26/2016 |
| T9 | 109 | 6/24/2018 |
| T18 | 118 | 6/24/2018 |

## Discrepancies and implications for existing documents

| Existing document / observation | Original-file finding | Disposition |
| --- | --- | --- |
| Source audit: portal showed 130 displayed rows including one blank | CSV has 129 data records and no blank record; 130 includes the header | Record the discrepancy. Do not add a blank row or drop the last real record. Cause of portal rendering difference remains unverified. |
| Source audit: CSV listed as 16.2 KB | Actual size 16590 bytes; approximately 16.20 KiB | Compatible with a rounded display; portal KB convention is not proven. |
| Source audit and dictionary: whitespace-collapsed headers and values | Exact header 12 has trailing whitespace; several cells preserve repeated/trailing spaces | Preserve source strings, use separate lookup keys. B1–B10 values agree after documented display normalization. |
| Source audit/dictionary: rod strings were shown with CSV-style quote marks | Standard CSV decoding yields a single embedded quote; for example O1 line 48 = `1/4" clear rod` | Outer/doubled serialization quotes must not be copied as extra literal characters. No geometry-unit interpretation added. |
| Source audit: no duplicate test IDs, specified missing counts, unusual O2 and 2018 dates | Confirmed for the local CSV; additional negative CO magnitudes and 2016 dates documented here | These are observations, not scientific corrections. |
| Data dictionary: encoding/dialect and physical line locations unknown | UTF-8 BOM, comma/double-quote CSV established; single physical line per logical record | Future provenance can use original physical line + column and exact hash. |
| Data dictionary: DOCX/XLSX definitions and scientific mappings unresolved | Both documents pending acquisition | No new definitions, unit conversions or condition mappings can be established. |
| Ingestion plan: acquire original bytes and reconcile ten records | Both CSVs hashed and B1–B10 reconciled; source version/download time still unverified | CSV portion of acquisition is verified locally; documentation and full cross-file review remain pending. |
| Ingestion plan: blank-row handling proposed | This CSV contains no blank logical record | Keep generic handling as a future parser requirement, but do not claim this file tests that case. |

All three Milestone 2A documents were read and left unchanged. This report records discrepancies rather than silently revising historical browser observations.

## DOCX and XLSX inspection status

The user explicitly confirmed that the ReadMe and Test Matrices have not been downloaded and instructed that they not be searched for or reconstructed. No further search was performed after that clarification.

**DOCX pending:** data definitions, experimental procedures, variable meanings, unit definitions, missing-value conventions, instrument settings and limitations. No page or paragraph locations can be supplied without the document.

**XLSX pending:** all worksheet names, headers, used ranges, formulas, cached values, units, experimental-condition mappings and test-identifier relationships. The workbook has not been assumed to match the CSV. No formula recalculation or spreadsheet export occurred.

## Unresolved questions and next step

Acquire the two named documents when ready, then inspect them read-only and compare their definitions and test mappings to this hashed CSV. Resolve source version and acquisition timing only with evidence. Until then, GMT, display-to-flow mappings, OR/over, sample suffix conventions, calibration and the scientific meaning of unusual readings remain unresolved. The table's gas units are recorded from the headers, not independently validated.

No ingestion pipeline, normalized dataset, database, RAG, frontend/backend change, Git commit or push was created. The only project outputs for this step are the manifest and this report. Originals remain at their actual Downloads paths with unchanged hashes.


## Milestone 2B-2 acquisition and reconciliation addendum

Checked 2026-11-05T12:00:46.810348+00:00. Earlier milestone statements above are preserved as history. The latest user request authorized new official-source acquisition attempts; the previous instruction not to search for undownloaded documents is not treated as a claim that they exist locally.

NASA Version 4 lists the ReadMe (21.03 KB) and Test Matrices (28.28 KB), both dated Tue Nov 25 2025, in Science Documents. These rounded display sizes are not acquired-byte measurements.

The ReadMe was selected and Download clicked. The download listener returned `Timed out after 20000ms waiting for download.` The workbook was then selected alone and Download attempted with a 20000 ms listener; the browser operation ultimately returned `js execution timed out; kernel reset, rerun your request` (tool-reported duration 249.405 seconds). No local download path or original document bytes were returned. The ReadMe file-tree anchor had no href. No actual download URL was captured. A page console TypeError about an undefined length was observed, but its causal relationship to the download failures is unknown. These are failures of this acquisition attempt, not evidence that NASA has removed or corrupted the documents.

Both documents are **pending_manual_download**; actual download URLs, original sizes, hashes and retrieval dates remain null. Neither is classified as corrupted or structurally invalid, because no bytes were available to inspect. No original placeholder, text reconstruction, workbook table, sheet inventory or document section inventory was created.

Open [NASA PSI-25](https://psi.nasa.gov/physci/repo/data/investigations/PSI-25), expand **Data files and documents → Science Documents** using the folder icon, select only the required filename, then click **Download**. Save the original bytes under `data/raw/bass_ii/original/` with the listed filename. Repeat for the other document. Do not re-save through Word or Excel. Subsequent verification must record the actual download URL, byte size, SHA-256 and retrieval time, then check the OOXML package and inspect its content.

The [ReadMe acquisition note](source_extracts/bass_ii_readme_extracted.md), [workbook acquisition note](source_extracts/bass_ii_test_matrices_inspection.md), [17-field reconciliation](bass_ii_field_reconciliation.md) and [anomaly investigation](bass_ii_anomaly_investigation.md) provide traceability. Counts: 0 confirmed, 0 partially confirmed, 17 unresolved, 0 not applicable. All five anomaly groups remain unresolved by supporting documentation.

CSV SHA-256 remains `71e792bf6b5fb5ea620c5dd70fbbac05515992e12aefcf5dff47312caa48c042` (16590 bytes). Independent CSV-to-JSONL comparison confirms 129 records, all 17 exact headers and all 2193 raw cell strings. Parser modules and both processed artifacts remain byte-identical. No parser defect was found or change proposed. The manifest preserves CSV entries and snapshots previous supporting-document entries before recording this attempt.

Scientific reconciliation remains blocked on acquisition; the transparent-failure branch of Milestone 2B-2 is documented. Milestone 3 should not assume a scientifically confirmed dictionary. No application functionality, analytics, database, AI, commits or pushes were introduced.

### Final verification

`backend/.venv/Scripts/python.exe -m pytest -q` from `backend`: **40 passed, 1 warning**, including all 31 parser tests and 9 other backend tests. The existing warning concerns deprecated httpx usage by Starlette TestClient. Restricted execution stalled without output; the identical suite passed outside that restriction. Final hashes again match the baseline for the original CSV, all parser modules and both processed artifacts. Supporting-document hash/open checks could not run because neither original was acquired.


## M2B-2R — supplied originals and scientific reconciliation

Sources throughout: CSV = `PSI-25_Experimental table_BASS-II.csv`; FAQ = `BASS-II data FAQ.docx`; workbook = `BASS-II Test Matrix by PI Final.xlsx`. These shorthand names always refer to the immutable files in `data/raw/bass_ii/original/`, with hashes in the [manifest](../data/manifests/bass_ii_acquisition_manifest.json). CSV rows include the header (B1 is row 2). Worksheet references preserve actual names, including `T'ien`.

FAQ page references use the file's saved Word pagination, not a new render: six `lastRenderedPageBreak` markers agree with seven pages in document properties. Exact paragraph IDs and complete text are in the [extraction](source_extracts/bass_ii_readme_extracted.md). Fresh rendering was unavailable because LibreOffice was not installed. The user-supplied filenames and expected portal aliases are recorded separately; hash agreement is with user-provided baselines, not an independently published NASA checksum.

Verified 2026-11-05T16:38:17.882185+00:00. This section supersedes earlier pending-acquisition statuses while preserving their history. All three provided hashes match the requested baselines. Existing canonical CSV bytes were compared and retained; DOCX and XLSX were copied byte-for-byte under their actual supplied filenames. The expected portal names are aliases only, not silently created substitute originals.

| Actual filename | Bytes | SHA-256 |
| --- | --- | --- |
| `PSI-25_Experimental table_BASS-II.csv` | 16590 | `71e792bf6b5fb5ea620c5dd70fbbac05515992e12aefcf5dff47312caa48c042` |
| `BASS-II data FAQ.docx` | 21538 | `69f32647792f54ab2a561e3cdafc6c87d854564fe487aed2b09265286bd84e1d` |
| `BASS-II Test Matrix by PI Final.xlsx` | 28956 | `1a3b283dd0adec861793bbc4a454aab64d398cd32d6f37d7a1ad0f642879e686` |

Original download URL and retrieval timestamp remain unknown; verification time is not download time. The local supplied documents match user-provided hashes; this does not independently authenticate their byte identity with the differently named portal objects. Both OOXML ZIPs passed CRC and XML structural checks; the workbook opened read-only. FAQ full text extraction retained 87 paragraphs across seven saved pages. Fresh rendering was unavailable because LibreOffice was missing; saved page/paragraph references are explicit throughout.

### Findings

All six worksheets were inspected: Bhattacharjee A1:P23 (22 records), Ferkul A1:P5 (4), Miller A1:P21 (20), Olson A1:P28 (27), Fernandez-Pello A1:P28 (27), and T'ien A1:P30 (29). All are visible, with no merged cells, formulas or comments. Exact PI/test-ID joins account for all 129 CSV and all 129 workbook records once each, with coordinates in the [mapping](bass_ii_test_matrix_mapping.md). Original values and Excel date/number representations are retained in [evidence JSON](source_extracts/bass_ii_workbook_evidence.json).

The four requested fields have 236 presentation differences: 189 comma/space, 41 case plus comma/space, and six explicitly reviewed word-order differences. No additional content or numeric disagreement was found. Agreement is not independent measurement validation. Thirteen negative initial CO readings and all five unusual final O2 values are corroborated in both sources, but their scientific causes remain unresolved.

FAQ pp. 1–2 paragraphs 13–25 now establishes Date/GMT, identifier conventions, restrictor, voltage/pot/air distinctions, uncalibrated gain, Nikon frame-count scope, daily O2 correction context, CDM/CSA-CP identities and OR >1000 ppm. Olson B1 explicitly supports the three 2016 tests (A26:C28); T'ien A9/A18's 2018 dates conflict with its B1 GMT 2014 label and remain unresolved. Detailed claim-level citations appear in the [field reconciliation](bass_ii_field_reconciliation.md) and [anomaly investigation](bass_ii_anomaly_investigation.md).

Field-definition statuses: **7 confirmed, 7 partially_confirmed, 3 identifier_only, 0 unresolved, 0 not_applicable**. Eight quantitative_candidate fields have explicit cell-level gates in the [suitability assessment](bass_ii_analytical_suitability.md). These labels are FLARE engineering judgments, not NASA validation. The [dictionary](bass_ii_data_dictionary.md) has been updated; prior provisional reports are retained under `docs/history/m2b2_before_reconciliation/`.

### Verification and remaining limits

129 records, 17 exact headers and 2,193 raw strings independently match the unchanged parser output. All three supplied and repository source hashes match. Parser modules, parser tests, other backend tests and both processed artifacts remain byte-identical to their pre-reconciliation baselines. Existing suite: **40 passed**, including 31 parser tests, with one existing Starlette/HTTPX deprecation warning. Restricted execution stalled; the identical suite passed in the approved execution context. No parser change or defect is proposed.

The prior automatic approval review failed due to a usage limit, not an unsafe-action finding. Work resumed within normal workspace permissions; the later test escalation succeeded. No unresolved permission requirement remains.

No database, frontend/backend feature, synthetic data, predictive model, RAG, risk score, Git commit or push was introduced. Next work should retain semantic evidence separately from lexical parser output and obtain scientific review for the open anomalies, calibration and validity gates before quantitative comparisons. No additional ingestion or analytics implementation is part of this milestone.
