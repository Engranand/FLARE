# BASS-II source-preserving CSV parser

Milestone 2B-1, verified 2026-11-05. The offline parser produces **129 records with 17 cells each**, preserving all **2,193 decoded raw cell strings** and exact headers. This is data-engineering verification, not scientific validation. ReadMe DOCX and Test Matrices XLSX remain pending acquisition.

## Run

From the repository root in PowerShell:

```powershell
cd backend
.\.venv\Scripts\python.exe -m app.ingestion.bass_ii
.\.venv\Scripts\python.exe -m pytest tests/test_csv_parser.py -q
.\.venv\Scripts\python.exe -m pytest -q
```

Use the existing stable Python 3.12 virtual environment; the machine's default Python previously pointed to an incompatible alpha. On Linux/macOS use `.venv/bin/python`. The command finds the repository root from its module location, independently of the current directory. `--root <path>` accepts another checkout with the same canonical relative source location. No network or credentials are required. No new dependencies were added.

## Source verification

Canonical input:

`data/raw/bass_ii/original/PSI-25_Experimental table_BASS-II.csv`

One downloaded copy was copied byte-for-byte from the manifest-recorded Downloads location without editing or re-saving it. The duplicate download is not parsed. Size: **16,590 bytes**. Expected and observed SHA-256:

```text
71e792bf6b5fb5ea620c5dd70fbbac05515992e12aefcf5dff47312caa48c042
```

The acquisition manifest now has a `canonical_copy` entry while retaining historical download inspections and pending-document entries. Download time and NASA source version remain unknown. Local hash matching establishes byte identity, not independent publisher authentication.

The dataset command requires this hash, the exact 17-header tuple (including spaces), and 129 data records. It stops on unavailable input, wrong hash, schema mismatch or incorrect record count. No replacement source is downloaded or reconstructed. Reading uses one verified byte snapshot; the source hash is checked again before writing outputs.

## Architecture and files

| File | Responsibility |
| --- | --- |
| `backend/app/ingestion/csv_parser.py` | Generic typed source/row containers, verified byte reading, strict CSV decoding, exact header and row-width checks, physical/logical locations |
| `backend/app/ingestion/classification.py` | Deterministic lexical categories and quality flags |
| `backend/app/ingestion/reporting.py` | Record serialization model, per-column/overall counts, duplicate checks and output writing |
| `backend/app/ingestion/bass_ii.py` | Dataset-specific hash, exact headers, expected count, warnings and CLI |
| `backend/app/ingestion/__init__.py` | Package boundary |
| `backend/tests/test_csv_parser.py` | Temporary technical CSV fixtures and regression tests |
| `data/manifests/bass_ii_acquisition_manifest.json` | Existing manifest extended with canonical-copy evidence |

The ingestion module README and raw/processed directory notes describe the implemented scope. No API routes, frontend behavior or other backend features changed. No database, analysis or AI integration exists.

The generic reader accepts dataset ID, source root/path, expected hash, identifier header, optional expected headers/count, encoding and delimiter. BASS-II configuration is isolated from generic parsing. This is a small-file in-memory parser; bulk media/large-dataset streaming is outside its scope. Future datasets require explicit source verification and configuration rather than guessing their schema or dialect.

## Input and raw preservation

BASS-II is UTF-8 with BOM, comma-delimited, double-quoted CSV with doubled embedded quotes. CRLF line endings are preserved inside quoted fields. CSV decoding removes structural quoting/BOM but does not strip, case-fold or convert header/cell strings. For example, a serialized doubled quote becomes one literal quote as required by CSV syntax. The immutable original retains the exact byte serialization and can be located by its hash.

A raw empty string stays `""`; `none`, `OR`, `over`, negatives, bounds, repeated spaces and trailing spaces remain strings. No numeric values, units or derived variables are emitted. Original header order is retained both in the header list and ordered cells object.

Duplicate exact headers and whitespace-only/empty headers are rejected to prevent object-key overwrites or ambiguous addressing. Missing identifier headers, decoding errors and malformed CSV raise SourceError. A short, long or zero-field blank row fails with CSV record and physical line information. A full-width row containing only empty cells is retained and flagged, not discarded. The verified source has no such blank rows.

## Classification rules, in precedence order

Classification uses a trimmed working copy only. Original strings never change. Matching is case-sensitive for special tokens.

| Category | Rule |
| --- | --- |
| `empty` | Exactly the empty string; whitespace-only text is not empty |
| `literal_none` | Trimmed text exactly `none` |
| `ambiguous_token` | Trimmed text exactly `OR` or `over`; meanings unresolved |
| `numeric` | Whole-string signed decimal syntax, optionally scientific notation, with no leading minus sign |
| `negative_numeric` | Same numeric syntax with a leading minus sign; includes lexical `-0` without assigning a physical meaning |
| `censored_numeric` | Whole-string `<`, `>`, `<=` or `>=` followed by numeric syntax; bound stays raw text |
| `compound_text` | Two or more numeric tokens separated by whitespace, comma, semicolon or `>`; lexical sequence only |
| `other_text` | All remaining strings, with `unclassified_text_review` flag |

Dates, identifiers, dimension descriptions and annotated settings may be other_text. `2 <1`, `10 max` and `3 5 approaching 10` conservatively remain other_text; this avoids pretending that qualifiers or quantities have a known grammar. `250>50` is a compound sequence; `>500` is a censored token. These categories are not measured-variable types. A numeric sample ID remains an identifier, and a censored Air display value is not thereby a calibrated velocity.

Any category other than numeric has an explanatory flag. Leading/trailing whitespace used during classification adds `classification_whitespace_normalized`. Whitespace-only input gets `whitespace_only_not_empty`. Row flags aggregate cell flags plus missing/duplicate test IDs, duplicate complete rows or all-empty rows where applicable. No range-based scientific correction or inference is performed.

## Output and provenance model

Outputs:

- `data/processed/bass_ii/bass_ii_records.jsonl`: one UTF-8 JSON object per source data record.
- `data/processed/bass_ii/bass_ii_quality_report.json`: UTF-8 quality summary.

Each record has dataset_id `BASS-II`, parser_version, source filename/hash/repository-relative POSIX path, record_provenance, cells and quality_flags. Provenance includes the one-based data row, CSV logical record number including the header, physical line start/end, original Test # and ordered exact headers.

The stable row ID is `dataset_id:sha256:record:csv_record_number`. It distinguishes rows even when Test # repeats, and changes when source bytes change. The cells object is keyed by the exact header; each value also includes original_header, one-based column_index, raw_value, classification and quality_flags. The cell inherits source/row provenance from its enclosing record. No Test # is used as the sole identifier.

Quality reporting counts all eight categories for every column and overall, including zeros; therefore empty, literal-none, negative, censored, ambiguous and compound counts are explicitly available. It includes total cells, duplicate exact nonempty Test # groups with data-row positions, duplicate complete raw-row groups, missing test-ID rows, row-width validation, parsing_errors and unresolved-scientific-interpretation warnings. Duplicate checks preserve case/whitespace and do not collapse reused sample IDs or a/b test suffixes.

Determinism: no run timestamps or machine-absolute paths appear in generated outputs; iteration order, flags and JSON formatting are stable. The parser version records the rules used. Changed classification rules require a version increment and regeneration. Raw and processed files stay excluded by the existing `.gitignore`; the committed-code workflow is not changed and no commits were made.

## Error and write behavior

Validation finishes before either output is written. CLI failures emit structured JSON on stderr with parsing_errors and return exit code 1. No partial parsed dataset is published after source/schema/row validation failure. Any older successful output remains unchanged, so the caller must check exit status rather than assume an existing output belongs to a failed run. Successful report parsing_errors is an empty list.

Output paths cannot alias each other or the input file. The writer rechecks source hash before serialization. Writes are sequential, not a two-file transaction: an OS/disk failure during writing may leave an incomplete pair; the command reports failure and a successful rerun is required. Never treat an interrupted run as successful. The source itself is only opened for reading by the parser.

## Actual verification results

- **40 tests passed:** 31 new parser tests plus 9 existing API/configuration tests.
- Existing upstream Starlette warning about HTTPX TestClient deprecation remains; no tests failed.
- Temporary fixtures cover requested categories, unknown/whitespace-only strings, exact headers/whitespace, quoted commas/newlines, logical versus physical record numbering, duplicate IDs/rows, malformed widths/headers/CSV/encoding, hash/schema/count mismatch, output validity/consistency, deterministic reruns and source-overwrite/change protection.
- Real output: **17 headers, 129 records, 2,193 cells**. Independent CSV decoding matched every original header and all raw values exactly.
- **170/170 B1–B10 fields** still match the source audit under its documented display-whitespace comparison. Original output strings were not normalized for that comparison.
- Source SHA-256 remains unchanged after parsing and verification. Unique stable row IDs: 129.
- No duplicate Test # values or duplicate complete rows. All rows have width 17; no parsing errors.
- No Python lint/type-check tool is configured in backend/pyproject.toml; no unconfigured tool was added or claimed to run.

| Overall classification | Count |
| --- | ---: |
| numeric | 1296 |
| negative_numeric | 13 |
| empty | 19 |
| literal_none | 16 |
| censored_numeric | 2 |
| ambiguous_token | 4 |
| compound_text | 91 |
| other_text | 752 |

The two censored tokens are M5 Final CO (ppm) `>500` and M12 Air display `<1`. Only the former is in a gas column. Counts are lexical cell counts across identifiers and settings as well as readings, not counts of scientifically comparable measurements.

## Remaining limitations

ReadMe and Test Matrices are still pending. Calibration, unit meanings beyond explicit headers, GMT, display mappings, OR/over and physical interpretations of anomalous readings remain unresolved. Existing 2A/2B-0 source findings are not silently corrected. No fire-risk scores, predictions, flame-spread computations, experiment rankings, frontend population, database or RAG were added. Successful parsing does not establish scientific validity.
