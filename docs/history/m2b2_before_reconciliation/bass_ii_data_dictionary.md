# BASS-II source-grounded data dictionary

Milestone 2A, 2026-11-05. **Proposed FLARE model, not NASA's validated schema.** Based on the live Version 4 [PSI-25 experimental table](https://psi.nasa.gov/physci/repo/data/investigations/PSI-25), selected file `PSI-25_Experimental table_BASS-II.csv`. File bytes and supporting-document contents remain unverified. See the [audit](bass_ii_source_audit.md) for exact records, locations and limitations.

## Observed source columns and proposed mappings

Column positions below are one-based in the rendered table. Header whitespace is collapsed in this mapping only. DOM text showed additional spaces in `Radiometer gain   (1000   250   50   10)` and `Calibrated  initial O2 % by vol`; future extraction must preserve the original header separately from its lookup key.

| Position / original column | Proposed normalized destination | Observed representation and original unit | Interpretation and constraints |
| --- | --- | --- | --- |
| 1 PI | Experiment.pi_raw | String; no unit | Preserve source spelling; not a globally unique person identifier |
| 2 Test # | Experiment.source_test_id | String, e.g. B1, P22a, T28b | Preserve case and suffix; never cast to integer |
| 3 Date | Experiment.date_raw; optional date_iso | Slash-form date, e.g. 2/19/2014 | Format appears month/day/year; explicit validated parse rule required, raw retained; 2018 entries need review |
| 4 GMT | Experiment.gmt_raw | Numeric-looking text such as 50, 188; header has no unit/definition | Do not reinterpret as timestamp or day-of-year until documentation confirms |
| 5 Sample # | Experiment.source_sample_id | String such as 147, 153m, 185M | Preserve suffix/case; repeats are permitted; not an experiment key |
| 6 Fuel Sample Material | Condition: fuel_sample_description | Free text; embedded micron, mm, cm and quote-mark rod dimensions | Material and geometry are combined; parse only explicit, reviewed facts with evidence spans |
| 7 Flow restrictor | Condition: flow_restrictor_setting | Codes such as 0, 1, 2; no unit | Code meaning unverified; 0 is a real source token, not missing |
| 8 Fan display | Condition: fan_display_setting | Scalar-looking text, sequences, pot annotations and ignition/extinction notes | No general unit established; some cells explicitly annotate 5cm/s; preserve full cell and qualifiers |
| 9 Air display | Condition: air_display_setting | Numbers, sequences, <1, max, ext, (?) and blanks | Header does not specify a velocity unit; do not rename all values airflow_cm_s |
| 10 Radiometer gain (1000 250 50 10) | Condition: radiometer_gain_setting | Scalar or transitions such as 250>50>250 | Instrument setting, not measured radiant flux; calibration not inspected |
| 11 Total Frames Shot | Experiment.frame_count_raw; optional integer frame_count | Count or literal none | Frames, not fps; none must not become 0; capture completeness unknown |
| 12 Calibrated initial O2 % by vol | Measurement: oxygen_concentration, phase=initial | Original unit `% by vol`; decimal text | Preserve calibrated label; calibration method and uncertainty unknown |
| 13 Calibrated final O2 % by vol | Measurement: oxygen_concentration, phase=final | `% by vol`; decimal or none | Final is a source phase, not an inferred timestamp |
| 14 Initial CO2 % by vol | Measurement: carbon_dioxide_concentration, phase=initial | `% by vol`; decimal or none | Do not convert to mole fraction or ppm silently |
| 15 Final CO2 % by vol | Measurement: carbon_dioxide_concentration, phase=final | `% by vol`; decimal, blank or none | Blank and literal none remain distinguishable |
| 16 Initial CO (ppm) | Measurement: carbon_monoxide_concentration, phase=initial | `ppm`; decimals, negative values, OR, none | Preserve ppm basis as unspecified; do not assume mass/volume basis from another column |
| 17 Final CO (ppm) | Measurement: carbon_monoxide_concentration, phase=final | `ppm`; decimals, >500, OR, over, none or blank | Censored/ambiguous values require typed status, not forced numeric conversion |

The dictionary names canonical quantities for organization; it does not certify measurement accuracy or support conversions.

## Requested scientific variables: presence and evidence

| Variable | Actual source evidence | Safe representation now |
| --- | --- | --- |
| Fuel material | PMMA, Nomex natural (nomex III), Japan Wax candle, SIBAL and incomplete descriptions occur in material cells | Raw description mandatory; canonical material nullable, with an explicit source span when assigned |
| Sample geometry | Films, slabs, rods and spherical sections described in text; micron/mm/cm and quote-mark dimensions | Preserve text and each explicitly stated dimension/unit; do not assume every length is width or thickness |
| Flow velocity | P5 row 79 Fan display includes `Fan pot 1.5 (5cm/s)`; P9/P13a/P13b also include 5cm/s annotations | Cell-specific annotated value may later be extracted with provenance. It is not a universal conversion of fan/air display settings |
| Flow direction | Investigation prose mentions opposed and concurrent flow; no dedicated per-test table field | Unknown per test until operations/test-matrix evidence is read; never infer from PI or material |
| Oxygen concentration | Initial/final calibrated O2 columns | Reported `% by vol`, raw strings plus optional parsed decimals |
| Carbon dioxide | Initial/final CO2 columns | Reported `% by vol`; missing tokens retained |
| Carbon monoxide | Initial/final CO columns | Reported `ppm`; preserve negative/censored/ambiguous tokens |
| Ignition conditions | M15 row 41 has `ignited 10` in Fan display; T23 row 122 has `moved igniter`; T24 row 123 has `top side ign` in material | Qualitative annotations only; no inferred time, power, temperature or full protocol |
| Flame spread | Investigation/publication descriptions discuss it; no dedicated spread-rate column in this table | Not represented as a measured variable here; no extraction from unreviewed video or paper prose |
| Extinction | `ext`, `extinguished`, `down to ext` occur in settings | Retain textual observation; no numerical extinction velocity, threshold or event time without reviewed context |
| Test identifiers | Test # and Sample # are separate columns | Preserve complete original strings and relation to row |
| Missing/incomplete values | Empty, none, incomplete descriptions, undefined setting units | Distinguish source missingness from parser errors and unknown semantics |

## Recommended normalized entities

Use a small source-preserving model, with no database choice required at this stage. Relations: Investigation → Experiment → Condition/Measurement. ResearchDocument and DataProvenance are linked through Evidence. One source row can produce multiple conditions and six phase-specific gas values, including explicit missing-value entries.

| Entity | Proposed fields and types | Mapping back to NASA |
| --- | --- | --- |
| Investigation | id:string; source_id:string; source_title:string; doi:string; source_version:string; landing_url:string; agency_raw:string; platform_raw:string; metadata_dates_raw:object; license_label:string; citation_raw:string; provenance_id:string | Header, Description → Project, Version History and Cite this Investigation. PSI-25 is separate from related PSI-26; each metadata field gets its own source locator |
| Experiment | id:string; investigation_id:string; source_test_id:string; source_sample_id:string; pi_raw:string; date_raw:string; date_iso:nullable date; gmt_raw:string; frame_count_raw:string; frame_count:nullable integer; source_row_id:string; provenance_id:string; quality_flags:string[] | Exact table columns 1–5 and 11, plus row ordinal and source file/version. Proposed identity includes investigation + version + table + PI + complete test ID; detect collisions rather than overwrite |
| Condition | id:string; experiment_id:string; condition_key:string; original_variable_name:string; original_value:string; original_unit:nullable string; unit_status:enum; parsed_value:nullable typed value; source_phase:nullable string; evidence_id:string; provenance_id:string; quality_flags:string[] | Columns 6–10. Preserve each complete free-text cell. Derived material/dimension/flow annotations reference the exact parent cell and span; cannot replace the raw cell |
| Measurement | id:string; experiment_id:string; quantity_key:string; source_phase:initial/final; original_variable_name:string; original_value:string; original_unit:nullable string; value_kind:enum; numeric_value:nullable decimal; comparator:nullable string; bound_value:nullable decimal; missing_reason:nullable enum; evidence_id:string; provenance_id:string; quality_flags:string[] | One entry per source gas column 12–17. Unit comes from that column header. No generated time axis, mean, uncertainty or unit conversion. Blank cells still have a provenance-bearing missing entry |
| ResearchDocument | id:string; investigation_id:string; title_raw:nullable string; original_filename:nullable string; source_url:string; doi:nullable string; authors_raw:nullable string; document_role:enum; content_status:enum; provenance_id:string | File-tree entries and publication listing are different evidence classes. A title/DOI listing is not proof that full text was inspected; filename nullable for DOI-only publications |
| Evidence | id:string; investigation_id:string; experiment_id:nullable string; document_id:nullable string; provenance_id:string; evidence_kind:table_cell/table_annotation/document_passage/media_listing/metadata; original_excerpt:string; source_location:object; verification_status:enum; verification_scope:string; reviewed_at:datetime | Exact cell/header, metadata field, document page/table or media frame/time. Bibliographic statements never populate an experimental measurement automatically |
| DataProvenance | id:string; investigation_source_id:string; source_test_id:nullable string; original_filename:nullable string; filename_aliases:string[]; source_url:string; source_version:string; source_location:object; original_variable_name:nullable string; original_value:nullable string; original_unit:nullable string; extraction_method:string; verification_status:enum; verification_scope:string; observed_at:datetime; retrieved_at:nullable datetime; sha256:nullable string; byte_size:nullable integer; parser_version:nullable string; license_label:nullable string; transformation_history:array | Retains source identity, original cell and extraction history. For this audit: rendered-table DOM observation; checksum/retrieval fields unknown. Future raw-file extraction must include actual immutable file hash and byte location |

IDs generated by FLARE must never be presented as NASA identifiers. A source revision creates a new versioned provenance record; do not overwrite earlier evidence. Case-folding sample IDs or stripping test suffixes must not be part of identity normalization.

### Required provenance for every extracted measurement

Each Measurement must link to a non-null provenance record containing investigation ID, complete experiment/test ID, original filename, official source URL, exact original variable name, original value, original unit, extraction method, source location and verification status. Keep the unit even when a value is missing (`none` CO still belongs to a ppm-labeled column). Explicitly represent an unstated unit as null plus `unit_status=not_stated`, never silently default it.

A source location should include source version, file/table name, table selection, one-based displayed row and column index/name; later add CSV logical record number and physical line span or XLSX sheet/cell. Displayed row 2 is not automatically CSV line 3: quoting and embedded line breaks must be checked from bytes. For this audit, B2 final CO is located by PSI-25 v4 → selected CSV → displayed data row 2 → column 17, plus Test # B2. This redundant locator survives sorting better than an ordinal alone.

Signed download URLs must not be committed as provenance. Store the canonical landing URL, exact directory path, observed object path if relevant, and safe filename aliases; keep temporary authorization in memory only. SHA-256 stays null until actual file bytes are acquired; never hash this Markdown transcription and label it a NASA file checksum.

### Value and verification semantics

- `value_kind=numeric`: source is a valid decimal lexeme; preserve its lexical form and precision. A numeric `0` is reported zero, not missing; it does not prove absence below a detection limit.
- `value_kind=censored`: e.g. `>500`; store comparator `>` and bound 500, but numeric_value null. It is not a measured value of 500.
- `value_kind=missing`: blank and literal `none` remain separate missing_reason values, with original_value unchanged.
- `value_kind=unresolved_token`: OR/over; definitions must be sourced before assigning over-range semantics.
- `value_kind=text` or `compound`: sequences/qualifiers remain whole; do not manufacture equally spaced timestamps or average settings.
- `verification_status=verified` always requires verification_scope (e.g. rendered source transcription, raw file matched, scientific review). These scopes are not interchangeable. `unverified` or `needs_review` describes unconfirmed interpretation and anomaly handling independently of a correctly transcribed token.
- Raw value and unit are immutable. Any later conversion is an additional derived field with formula, input IDs, source/target units, conversion version and reviewer; never a replacement.

### Worked mappings using actual observed cells

| Source | Proposed representation | Limit |
| --- | --- | --- |
| B1 row 1, Initial CO (ppm), 0 | quantity=carbon_monoxide_concentration; phase=initial; original_value="0"; unit="ppm"; numeric_value=0 | Reported zero only |
| B2 row 2, Final CO (ppm), empty | phase=final; original_value=""; unit="ppm"; value_kind=missing; missing_reason=blank | No inferred value |
| B4 row 4, Initial CO (ppm), -1 | original_value="-1"; numeric_value=-1; flag=negative_reading_review | No clamping |
| M5 row 31, Final CO (ppm), >500 | original_value=">500"; comparator=">"; bound_value=500; numeric_value=null | Censored, not exact |
| O4 row 51, Final CO (ppm), OR | original_value="OR"; value_kind=unresolved_token | No assumed sensor range |
| B6 row 6, Air display, 3 5 approaching 10 | condition_key=air_display_setting; original text preserved; unit=null | Not three calibrated velocity measurements |

## Decisions still requiring documentation

CSV byte representation, XLSX sheet schema, unit calibration, display-to-flow mappings, flow direction per run, GMT definition, sample suffix meanings, OR/over definitions, radiometer settings, ignition protocol and scientific meaning of anomalous readings are unresolved. These are explicit constraints on Milestone 2B, not fields to fill heuristically.


## Milestone 2B-2 status addendum (2026-11-05)

The opening Milestone 2A statement about unverified CSV bytes is historical: the canonical CSV is now byte-verified with SHA-256 `71e792bf6b5fb5ea620c5dd70fbbac05515992e12aefcf5dff47312caa48c042`, UTF-8 BOM, 129 data records and 17 exact headers. All 2,193 parsed raw strings match it. See [source reconciliation](bass_ii_source_reconciliation.md). The two supporting documents remain unavailable after official-portal download attempts; no new scientific definition is justified. Existing proposed mappings remain proposals and parser classifications remain lexical. [Field reconciliation](bass_ii_field_reconciliation.md) records all 17 fields as unresolved for document corroboration; [anomaly investigation](bass_ii_anomaly_investigation.md) records the outstanding questions. Earlier descriptions such as instrument setting or frame count are header-based interpretations, not newly confirmed instrument definitions. No units, calibrated quantities or raw values were changed.
