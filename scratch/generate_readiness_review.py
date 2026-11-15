review_content = """# FLARE — Milestone 8 Ingestion Engine Readiness Review

**Milestone**: M8 — Ingestion Engine Implementation Readiness  
**Author**: FLARE Autonomous Scientific Data Engineer & Combustion Research Analyst  
**Audit Date**: 2026-11-14  
**Audit Scope**: Strict READ-ONLY Pre-Implementation Verification  
**Overall Verdict**: **NOT READY FOR M8 IMPLEMENTATION** (Blocked by Migration Lineage & Working Tree State)  

---

## 1. Executive Summary & Explicit Verdict

A comprehensive, read-only pre-implementation review was conducted to evaluate the scientific and technical readiness of the FLARE platform for **Milestone 8: Ingestion Engine Implementation**.

### Explicit Verdict
```
╔══════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                      ║
║                       VERDICT: NOT READY FOR M8 IMPLEMENTATION                       ║
║                                                                                      ║
║  The domain data schema (33 approved tables) is structurally ready to support        ║
║  BASS-II ingestion. However, implementation is BLOCKED by five critical engineering  ║
║  issues:                                                                             ║
║  1. Historical migration tampering in 0003_m43_sealing.py breaking Alembic replay.   ║
║  2. Uncommitted working tree state (10 modified files, 18 untracked files).          ║
║  3. Database drift risk: existing databases will fail with SQLSTATE 42P01.           ║
║  4. SECURITY DEFINER trigger privilege surface area & unlogged table caveats.        ║
║  5. Typographical hash discrepancies in M7 audit report Section 7.1.                 ║
║                                                                                      ║
╚══════════════════════════════════════════════════════════════════════════════════════╝
```

---

## 2. Verification of the Five M7 Deliverables

All five deliverables generated during Milestone 7 were independently verified against the physical files on disk, the master manifest (`resource_manifest.json`), and the official NASA PSI repository records:

| Deliverable | Verification Scope | Status | Findings & Audit Notes |
|---|---|---|---|
| **1. `scientific_dataset_inventory.csv`** | 261 resources across 26 investigations | **VERIFIED** | Exactly 262 lines (1 header + 261 resource rows). All columns populated with physical phenomena, attribution types, and compatibility ratings. All 261 SHA-256 digests match physical disk bytes. |
| **2. `scientific_dataset_profile.json`** | 261 deep structural and statistical profiles | **VERIFIED** | Valid JSON (525.0 KB). Contains detailed CSV row/column counts, column types, missing value frequencies, unit extractions, numeric min/max/mean ranges, and Excel sheet previews. |
| **3. `scientific_compatibility_matrix.md`** | 7 combustion capabilities evaluated across 15 study groups | **VERIFIED** | Establishes scientifically defensible cross-investigation comparability ratings. Includes rigorous non-dimensional scaling analysis proving why Saffire does not automatically validate BASS-II. |
| **4. `experimental_vs_simulated_attribution.md`** | Column-by-column breakdown of mixed datasets | **VERIFIED** | Formulates strict epistemological boundaries. Discovers that `PROCI_2019_Oscillatory_Cool_Flame.csv` and `PROCI_2019_Stable_Cool.csv` are 100% numerical simulations, and provides exact column slicing rules for PSI-117. |
| **5. `m7_scientific_audit_report.md`** | Master technical audit report | **VERIFIED (With Note)** | Exhaustive 28 KB technical synthesis. Documented Defect: Section 7.1 table contains placeholder SHA-256 strings for 5 priority files (e.g. `8390bbf4...` instead of `71e792bf...` for BASS-II). `inventory.csv` and `profile.json` contain the true disk hashes. |

---

## 3. BASS-II Review as Primary Quantitative Baseline

### 3.1. Scientific Apparatus & Physical Context
The NASA **BASS-II** (*Burning and Suppression of Solids — II*, Investigation ID: **PSI-25**) flight experiment evaluated the combustion, flame spread, and extinction limits of solid aerospace materials in microgravity aboard the International Space Station (ISS) Microgravity Science Glovebox (MSG).
- **Physical Environment**: Small forced convective flow duct ($7.6\\text{ cm} \\times 7.6\\text{ cm} \\times 17\\text{ cm}$) operating under microgravity ($10^{-4}$ to $10^{-6}\\text{ g}$).
- **Flow Control**: Airflow driven by a variable-speed fan through calibrated flow restrictor plates (0, 1, 2) yielding velocities $u_\\infty = 1.0\\text{ to } 5.5\\text{ cm/s}$.
- **Atmosphere**: Total pressure $P = 1.0\\text{ atm}$; oxygen concentration varied systematically from $13.6\\%$ to $22.2\\%$ by volume.

### 3.2. Investigation Sub-Studies (6 Science PIs)
BASS-II investigated 51 distinct fuel sample descriptions across 129 test runs (`B1` through `B129`), categorized across 6 Principal Investigators:
1. **Subrata Bhattacharjee**: Very thin PMMA films (100 and 200 $\\mu$m thick, 2 cm wide), igniting downstream for opposed flame spread.
2. **Paul Ferkul**: Nomex III fabric and cylindrical candle flames to conclude BASS-I testing.
3. **Fletcher Miller**: Thick PMMA slabs (1.2 cm and 2.5 cm thick; 1-sided and 2-sided burns), evaluating in-depth conduction and thermal inertia.
4. **Sandra Olson**: Clear cast PMMA rods (1/4\" and 0.5\" diameter), igniting upstream end for stagnation flame / concurrent flow spread.
5. **Carlos Fernandez-Pello**: Black PMMA rods (1/4\" and 0.5\" diameter), igniting downstream end for opposed flow flame spread.
6. **James T'ien**: SIBAL fabric (75% cotton / 25% fiberglass blend, 1 cm wide) and 4 cm PMMA spherical sections, evaluating low-speed radiative extinction limits.

### 3.3. Baseline Data Source Verification
The primary tabular data file is:
- **Filename**: `PSI-25_Experimental table_BASS-II.csv`
- **Location**: `data/raw/challenge_resources/original/bass_ii/PSI-25_Experimental table_BASS-II.csv` (and `data/raw/bass_ii/original/PSI-25_Experimental table_BASS-II.csv`)
- **File Size**: 16,590 bytes
- **SHA-256**: `71e792bf6b5fb5ea620c5dd70fbbac05515992e12aefcf5dff47312caa48c042`
- **Dimensions**: Exactly 17 columns and 129 data rows (130 total lines including header).
- **Integrity**: 0 duplicate rows; 129/129 unique `Test #` values (`B1` through `B129`). Reconciled 170/170 test records against `BASS-II Test Matrix by PI Final.xlsx`.

---

## 4. Field-Level Ingestion Mapping to Database Schema

The companion artifact [bass_ii_ingestion_mapping.csv](file:///c:/Users/anand/OneDrive/Documents/ChatGPT/FLARE/bass_ii_ingestion_mapping.csv) establishes the exact field-level mapping from the 17 CSV headers to the approved database schema (`backend/app/models/scientific.py`).

Below is the summary mapping across all 17 fields:

| Col | CSV Header (Raw) | Target Schema Entity | Target Column | Source Kind | Lexical Category | Stated Unit |
|---|---|---|---|---|---|---|
| **0** | `PI` | `observation` / `experimental_test` | `raw_value` / `metadata->>'pi'` | `text` | `text` | `not_stated` |
| **1** | `Test #` | `observation` / `experimental_test` | `raw_value` / `test_identifier` | `text` | `text` | `not_stated` |
| **2** | `Date` | `observation` / `experimental_test` | `raw_value` / `metadata->>'date'` | `text` | `text` | `not_stated` |
| **3** | `GMT` | `observation` / `experimental_test` | `raw_value` / `metadata->>'gmt'` | `numeric_lexeme` | `numeric` | `not_stated` |
| **4** | `Sample #` | `observation` / `experimental_test` | `raw_value` / `metadata->>'sample_number'` | `text` | `text` | `not_stated` |
| **5** | `Fuel Sample Material` | `observation` / `condition_component` | `raw_value` / `text_value` | `text` | `text` | `not_stated` |
| **6** | `Flow restrictor` | `observation` / `condition_component` | `raw_value` / `numeric_value` | `numeric_lexeme` | `numeric` | `not_stated` |
| **7** | `Fan display` | `observation` / `condition_component` | `raw_value` / `text_value` | `text` | `text` | `not_stated` |
| **8** | `Air display` | `observation` / `condition_component` | `raw_value` / `text_value` | `text` | `text` | `not_stated` |
| **9** | `Radiometer gain (1000 250 50 10)` | `observation` / `condition_component` | `raw_value` / `text_value` | `text` | `text` | `not_stated` |
| **10** | `Total Frames Shot` | `observation` / `experimental_test` | `raw_value` / `metadata->>'total_frames'` | `text` | `text` | `not_stated` |
| **11** | `Calibrated initial O2 % by vol ` | `observation` / `condition_component` | `raw_value` / `numeric_value` | `numeric_lexeme` | `numeric` | `% by vol` |
| **12** | `Calibrated final O2 % by vol` | `observation` / `condition_component` | `raw_value` / `numeric_value` | `text` | `numeric` / `none_literal` | `% by vol` |
| **13** | `Initial CO2 % by vol` | `observation` / `condition_component` | `raw_value` / `numeric_value` | `text` | `numeric` / `none_literal` | `% by vol` |
| **14** | `Final CO2 % by vol` | `observation` / `condition_component` | `raw_value` / `numeric_value` | `text` | `numeric` / `none_literal` | `% by vol` |
| **15** | `Initial CO (ppm)` | `observation` / `condition_component` | `raw_value` / `numeric_value` | `text` | `numeric` / `negative_numeric` / `ambiguous_or` | `ppm` |
| **16** | `Final CO (ppm)` | `observation` / `condition_component` | `raw_value` / `numeric_value` | `text` | `numeric` / `sensor_saturation` / `ambiguous_or` | `ppm` |

---

## 5. Epistemological Attribution of BASS-II Fields

Every column in `PSI-25_Experimental table_BASS-II.csv` was classified into its epistemological category:

```
                                  BASS-II COLUMN ATTRIBUTION BREAKDOWN
  ┌─────────────────────────────────┬─────────────────────────────────┬─────────────────────────────────┐
  │   EXPERIMENTAL METADATA (6)     │  RAW EXPERIMENTAL MEASUREMENT (8)│ REFERENCE / THEORETICAL (3)     │
  ├─────────────────────────────────┼─────────────────────────────────┼─────────────────────────────────┤
  │ - PI (Principal Investigator)   │ - Fan display                   │ - Fuel Sample Material          │
  │ - Test # (Test Identifier)      │ - Air display                   │ - Flow restrictor (0, 1, 2)     │
  │ - Date (Calendar Run Date)      │ - Calibrated initial O2 % vol   │ - Radiometer gain (multiplier)  │
  │ - GMT (Day of Year)             │ - Calibrated final O2 % vol     │                                 │
  │ - Sample # (Hardware Index)     │ - Initial CO2 % vol             │                                 │
  │ - Total Frames Shot             │ - Final CO2 % vol               │                                 │
  │                                 │ - Initial CO (ppm)              │                                 │
  │                                 │ - Final CO (ppm)                │                                 │
  └─────────────────────────────────┴─────────────────────────────────┴─────────────────────────────────┘
```

- **Derived Quantities in Raw CSV**: **0 columns**. Measured flame spread rates ($V_f$) and extinction velocities ($u_{\\text{ext}}$) are derived post-flight from raw video analysis, and do not reside in the baseline CSV.
- **Simulation Outputs in Raw CSV**: **0 columns**. BASS-II is 100% empirical spaceflight data with zero synthetic or computational model blending.

---

## 6. Provenance Preservation Strategy

To guarantee that no original scientific information is destroyed or altered during ingestion, FLARE enforces an uncompromised **Lossless Provenance Architecture**:

1. **Exact Literal Value Preservation**:
   - Every cell in the 129 $\\times$ 17 grid is preserved verbatim in `public.observation.raw_value` as text, including leading/trailing whitespace, literal `\"none\"`, negatives (`\"-1\"`), over-range markers (`\">500\"`, `\"over\"`), and ambiguities (`\"OR\"`).
2. **Deterministic Source Locators**:
   - Each record stores its 1-based source CSV row number in `public.source_record.source_record_number` (1 to 129).
   - An immutable string locator `source_row_id` is computed as:
     `\"BASS-II:71e792bf6b5fb5ea620c5dd70fbbac05515992e12aefcf5dff47312caa48c042:record:\" || source_record_number`.
3. **Cryptographic SHA-256 Anchoring**:
   - The original CSV bytes are verified against `71e792bf6b5fb5ea620c5dd70fbbac05515992e12aefcf5dff47312caa48c042` before ingestion begins.
   - The parse run is sealed into `public.aggregate_seal` using canonical SHA-256 member hashing and raw archive byte comparison (`flare_sealing.archive_matches()`).
4. **Stated Unit Preservation**:
   - Inferred units are strictly prohibited. Only units stated verbatim in headers (`% by vol`, `ppm`) are ingested with `unit_origin = 'field'`. All other fields are tagged `unit_origin = 'not_stated'`.
5. **Quality Flagging & Classification**:
   - Tokens such as `\"none\"` are categorized as `none_literal` (not NULL).
   - Negative values (`\"-1\"`) are categorized as `negative_numeric`.
   - Over-range tokens (`\">500\"`) are categorized as `sensor_saturation`.
   - Ambiguous tokens (`\"OR\"`) are categorized as `ambiguous_or`.

---

## 7. Scientific Ambiguities & Incompatible Experimental Conditions

The audit identified six critical scientific ambiguities that must not be normalized without explicit documentation:

1. **On-Board Computer Leap Year Bug**:
   - The BASS-II Readme explicitly warns: *\"Date: actual date of experiment. Video display is one day later than actual date due to a leap year the on-board computer did not account for.\"* The ingestion engine must preserve the recorded `Date` and `GMT` without reconciling them against video timestamps.
2. **Electrochemical Sensor Zero Drift**:
   - `Initial CO (ppm)` contains negative values (`-1`, `-2`, `-3`). These represent uncalibrated baseline drift of the electrochemical CO sensor. Clamping these values to zero would destroy sensor calibration lineage.
3. **Sensor Saturation**:
   - `Final CO (ppm)` contains `\">500\"` and `\"over\"`. The flight sensor full scale is 500 ppm. Ingestion must not parse these as `500.0` or `NULL`; they must remain saturated indicators of incomplete combustion.
4. **Ambiguous \"OR\" Values**:
   - Tests record `\"OR\"` for CO readings where the operator or ground telemetry recorded ambiguous or conflicting values.
5. **Uncalibrated Potentiometer Settings**:
   - `Fan display` and `Air display` are unitless operator settings (e.g. `62`, `47`, `.54 pot 0.45 pot`). They cannot be converted directly to flow velocities ($u$, cm/s) without applying polynomial calibration curves from `PSI-25_Reference Data_Fan calibration data.xlsx`.
6. **Incompatible Fuel Geometries**:
   - Thin PMMA films ($100\\ \\mu\\text{m}$, thermally thin) cannot be directly compared to thick PMMA slabs ($2.5\\text{ cm}$, thermally thick) or rods ($0.5\\\"$ cylinder) using a single 1D spread model. Each geometry operates under different Biot numbers ($Bi = h L / k_s$) and thermal conduction regimes.

---

## 8. Review of M6 Database-Security Remediation Concerns

During Milestone 6, an issue was raised regarding **GUC-based trigger memoization**:
- In the initial implementation of M4.3 aggregate sealing, `flare_sealing.check_parse()` avoided re-validating the same parse run during batch inserts by checking a PostgreSQL GUC setting: `current_setting('flare.parse_run_checked', true)`.
- **Vulnerability**: Any unprivileged database connection can set GUC parameters (`SET LOCAL flare.parse_run_checked = ...`), which could allow a malicious or buggy client to bypass parse shape validation.

### Remediation Evaluation:
The remediation replaced the GUC with an unlogged table and a `SECURITY DEFINER` function:
1. Created `flare_sealing.checked_parse (xact_id xid8, parse_run_id uuid, PRIMARY KEY (xact_id, parse_run_id))`.
2. Modified `flare_sealing.check_parse()` to `SECURITY DEFINER SET search_path = pg_catalog, flare_sealing, public`.
3. Checked deduplication using `INSERT ... ON CONFLICT DO NOTHING` inside the transaction.

### CRITICAL UNRESOLVED PROBLEM (Showstopper):
**The remediation was implemented by editing historical migration `0003_m43_sealing.py` and `m43_sealing.sql` in-place.**

```
                                  ALEMBIC MIGRATION TIMELINE CORRUPTION
    0001_m41_baseline
      └── 0002_m42_core_schema
            └── 0003_m43_sealing  <=== TAMPERED IN-PLACE! (Added checked_parse & SECURITY DEFINER)
                  └── 0004_m44_n1
                        └── 0005_variable_immutability
                              └── 0006_evidence_immutability
                                    └── 0007_m45_n2  <=== Alembic head on existing databases
```

- Any existing PostgreSQL database that has already migrated to revision `0003` or `0007` **will not re-run migration 0003**.
- Consequently, `flare_sealing.checked_parse` will not exist on deployed databases, and `flare_sealing.check_parse()` will not be updated.
- When M8 ingestion inserts rows into `observation`, the trigger will fail with:
  `ERROR: relation \"flare_sealing.checked_parse\" does not exist (SQLSTATE 42P01)`.
- In addition, running `SECURITY DEFINER` on a trigger that executes 2,193 times per BASS-II ingestion increases the privileged execution surface area.

---

## 9. Database Schema Capability Assessment

### Can the current approved database schema support BASS-II ingestion without modification?
**YES, from a domain schema perspective.**
The 33 approved domain tables defined in `backend/app/models/scientific.py` and provisioned by `0002_m42_core_schema.py` provide complete relational coverage:
- `investigation`: Stores BASS-II metadata (agency NASA, code PSI-25).
- `source_document`: Stores CSV, XLSX, and DOCX files with SHA-256 digests.
- `source_field`: Stores all 17 CSV columns with headers, ordinals, and units.
- `source_record`: Stores all 129 row locators and source line numbers.
- `observation`: Stores all 2,193 raw cell values with lexical categories.
- `experimental_test`: Stores all 129 test identifiers (`B1` to `B129`).
- `test_source_record`: Links tests to exact source CSV rows.
- `condition_segment`, `experimental_condition`, `condition_component`: Stores parsed fuel, restrictor, flow, and oxygen conditions.
- `aggregate_seal`: Cryptographically seals parse runs and experimental conditions.

**NO, from an operational migration perspective.**
Because historical migration `0003` was modified in place, running migrations on a pre-existing database will not install the necessary deduplication table, causing insert triggers to fail.

---

## 10. Final Readiness Verdict & Action Plan

### Final Verdict: **NOT READY FOR M8 IMPLEMENTATION**

Milestone 8 cannot proceed until the five blockers documented in [m8_blockers.md](file:///c:/Users/anand/OneDrive/Documents/ChatGPT/FLARE/m8_blockers.md) are resolved.

### Actionable Remediation Plan to Unlock M8:
1. **Restore Migration Lineage**:
   - Revert `backend/migrations/versions/0003_m43_sealing.py` and `m43_sealing.sql` to pristine state.
   - Create clean forward migration `0008_m6_security_remediation.py` to provision `flare_sealing.checked_parse` and update `flare_sealing.check_parse()`.
2. **Clean Working Tree**:
   - Run full pytest test suite against disposable test database.
   - Stage and commit verified M4/M5/M6 infrastructure files.
3. **Correct Documentation Typo**:
   - Update Section 7.1 of `m7_scientific_audit_report.md` with true disk hashes.
4. **Formally Transition Verdict**:
   - Upon completion of steps 1–3, update verdict to **READY FOR M8 IMPLEMENTATION** and begin BASS-II ingestion execution.
"""

with open("m8_readiness_review.md", "w", encoding="utf-8") as f:
    f.write(review_content)

print("Saved m8_readiness_review.md successfully.")
