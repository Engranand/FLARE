# BASS-II ingestion plan — proposed Milestone 2B

Date: 2026-11-05. **Plan only; implementation is not authorized by Milestone 2A.** Based on the [source audit](bass_ii_source_audit.md) and [source-grounded dictionary](bass_ii_data_dictionary.md).

## Recommended scope

Implement a small deterministic, provenance-first import of the verified experimental table after acquiring its original bytes and reviewing the supporting instructions. Defer bulk media, video analysis, scientific inference, RAG, databases and UI changes. No backend architecture change is needed for the audit.

The current evidence is sufficient to design a parser contract, but not to certify calibration, interpret all tokens, or conduct experiment comparisons. **129 identified rows plus one blank rendered row is an audit observation, not a permanent expected dataset count.** A different file revision or source-byte structure must be reconciled, not forced into this count.

## 1. Resolve acquisition and source identity before coding extraction

- Open PSI-25 Version 4 in the official portal. Record the DOI, displayed version/date, access date, license and citation. Preserve the distinction between portal version update date and individual file date-added metadata.
- Expand Experimental table using its folder icon, select only `PSI-25_Experimental table_BASS-II.csv`, confirm selection count and use the actual Download control. Milestone 2A's download capture timed out; successful byte retrieval is the first acceptance gate.
- Obtain the actual ReadMe DOCX, Test.Matrices XLSX and relevant operations/SRD documentation from the observed tree. Do not guess endpoints or construct S3 object paths. A manual, manifest-recorded acquisition is acceptable if no supported automated interface is documented.
- If downloads remain inaccessible, stop the acquisition step and report the exact failure. Request an authorized original file or seek NASA guidance only with permission to contact them; never substitute a fabricated CSV or reconstructed table and label it original NASA data.
- For each acquired file, retain exact filename, source directory, any download filename alias, canonical landing URL, source version, UTC retrieval timestamp, bytes, SHA-256, media type and access/license notes. Do not retain signed URL credentials in code, logs or committed manifests.
- Check archive size before acquisition. Do not bulk-fetch the portal's reported 255.77 GB. The B1 image ZIP alone is listed as 627.61 MB and is unnecessary for first table ingestion.

Deliverable: reviewed acquisition manifest plus immutable original files in the existing raw-data area. The existing Git ignore excludes raw files; do not alter it to commit large datasets. Manifest entries must not claim a file was acquired unless bytes and hash exist.

## 2. Reconcile source structure and semantics

- Determine actual encoding, BOM, delimiter, quoting, header row, logical-record boundaries and trailing blank records from the CSV bytes. Match the 17 observed columns; retain original header text and order before building whitespace-normalized lookup keys.
- Inspect workbook sheet names, ranges, merged headers, formulas versus cached values, notes and units. Do not assume the Test.Matrices workbook duplicates the public CSV.
- Read the README/operations/SRD for Fan display, Air display, Flow restrictor, GMT, radiometer settings, ppm basis, calibration and missing-token definitions. Record exact document page/section/cell evidence for each interpretation.
- Reconcile the ten B1–B10 records against original CSV cells. Confirm B2 blanks/none, B4 -1, and B6/B8/B9/B10 compound settings. Preserve mismatch reports; do not force raw files to agree with the portal rendering.
- Review P22a/P22b and T28a/T28b unusual final O2, and T9/T18's displayed 2018 dates. Seek documentary explanation; unresolved values remain unchanged and flagged.
- Verify file-to-test associations before media linkage. A B3-labelled video appeared under the B1 folder, so parent-directory inference alone is insufficient.

Deliverable: reviewed header/variable mapping and unresolved-interpretation register, including byte-versus-portal discrepancies.

## 3. Implement only the bounded table import after review

Use the existing `backend/app/ingestion/` boundary when Milestone 2B is approved. Avoid a general framework before one real parser is working.

1. Read an explicit local source path and manifest; validate checksum and source identity. Keep network acquisition separate from deterministic parsing.
2. Preserve raw row text/cells, exact original headers, logical record number and physical line span. Do not silently trim source values; normalized lookup keys are additional fields.
3. Create Investigation and Experiment records with complete test/sample IDs. Distinguish sample reuse from duplicate experiments; retain suffixes/case. Separate source-version identity from cross-version matching.
4. Map the six gas columns to initial/final Measurement entries. Retain original text and header unit. Classify numeric, blank, literal none, censored and unresolved tokens without imputing.
5. Keep material/geometry and flow/radiometer settings as source-preserving Condition entries. Only add separately evidenced parsed annotations; do not interpret all Air display values as cm/s.
6. Emit validation results and review flags alongside outputs. Quarantine structurally invalid rows; retain the full raw payload and reason. A blank row is logged as a structural exclusion, not an experiment. Scientific anomalies should remain visible as flagged source values rather than being silently dropped.
7. Produce local normalized artifacts and a provenance manifest under existing processed/manifests directories. Select a simple documented format during implementation; JSON Lines is suitable for structured provenance but is not yet an established project contract. No database is necessary.
8. Make reruns idempotent by source hash + parser/mapping version. Never overwrite raw files; keep output-version manifests and transformation history.

The frontend must continue to say not yet ingested until a real import passes review and a later explicitly scoped integration exposes it. Milestone 2B should not invent an experiments endpoint merely to populate the UI.

## 4. Quality rules and tests required in 2B

Tests use small, actual source-derived fixtures with attribution and provenance, not invented scientific measurements. Synthetic parser-edge strings may be used only as clearly labelled technical fixtures, separate from scientific data.

| Test/check | Acceptance criterion |
| --- | --- |
| Header/row shape | All expected columns mapped explicitly; unexpected/missing columns reported, not shifted silently |
| Original preservation | Raw values, headers, units and case round-trip without loss; derived values remain separate |
| Ten-record reconciliation | B1–B10 match original-source cells and audit locators, or discrepancies are explained in a review artifact |
| Missing versus zero | B1 CO 0 remains numeric zero; B2 blank final gases remain blank; frame-count none remains a literal source marker |
| Negative values | B4 initial CO -1 retained with a quality flag |
| Censored/token handling | M5 >500 stays a strict bound; O4 OR and O13b over stay unresolved unless documentation supports a mapping |
| Compound settings | B6/B8/B9/B10 retain all tokens, inequality/qualifiers and order; no invented timing |
| Identity | P22a/P22b and T28a/T28b remain distinct; sample reuse does not deduplicate runs |
| Blank row | Entirely blank source record is excluded with a logged reason and original location |
| Duplicate handling | Exact row and candidate-ID collisions reported; no silent overwrite; original-file results compared with rendered-table audit |
| Provenance coverage | Every measurement resolves to investigation/test/file/hash/header/value/unit/location/method/verification scope |
| Repeatability | Same source hash and parser version produce equivalent normalized output and quality report |
| Offline operation | Parsing tests need no NASA access, credentials or network; acquisition tests remain separate |
| Failure behavior | Hash mismatch, corrupted encoding or unexpected schema fails with actionable report and retains original bytes |

Report counts by source rows, identified records, blank exclusions, quarantined records, parsed values, source missingness and unresolved tokens. Do not describe all source records as scientifically validated merely because parsing succeeds.

## 5. Review gates and completion criteria

**Gate A — acquisition:** original CSV captured with verified checksum and citation; documentation access status explicit. If unavailable, 2B is blocked at acquisition, not completed by a portal transcription.

**Gate B — mapping:** 17-column mapping reconciled with bytes; missing/token policies reviewed; undefined flow units and scientific meanings remain null/flagged. Lack of calibration documentation can permit raw-preserving storage, but blocks interpreted flow comparisons.

**Gate C — reproducibility:** deterministic parser, source-based fixtures, full provenance coverage, idempotence and transparent quality/exclusion report pass automated checks.

**Gate D — handoff:** reviewer can trace each of at least ten records to immutable original bytes and see every unresolved anomaly. No fabricated values, silent conversions, scientific conclusions, API guesses, bulk-media ingestion or unrelated application changes.

Milestone 2B is complete when the bounded import and review artifacts meet these gates. Flow calibration, flame-spread/extinction analysis, media-derived measurements and research-gap inference require separate scientific review and later scope.

## Audit handoff status

Milestone 2A created only three Markdown documents. The live source's metadata and rendered table were accessible; original file downloads, supporting-document contents and scientific calibration remain unresolved. Review these documents before authorizing ingestion implementation.
