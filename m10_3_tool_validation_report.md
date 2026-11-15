# FLARE Milestone 10.3: Scientific Tool Validation Report

**Project**: FLARE — Scientific Intelligence Platform for Spacecraft Fire Safety  
**Milestone**: M10.3 — Scientific Tool Execution Layer  
**Document**: Tool Validation, Interface Contracts, and Edge-Case Audit  
**Date**: November 14, 2026  
**Status**: VERIFIED & AUDITED  

---

## 1. Tool Validation Overview

This report provides detailed validation records for each of the four tools implemented and registered under Milestone M10.3. Every tool adheres to deterministic type contracts, input boundary checks, and verifiable provenance requirements.

---

## 2. Tool 1: `m9_get_analytical_result`

### 2.1 Interface Contract
- **Input Parameters**:
  - `investigation`: `str` (default: `"PSI-25"`)
  - `metric_code`: `str | None` (optional specific target metric)
  - `protocol_code`: `str | None` (optional protocol scope)
- **Output Data Schema**: List of metric payloads containing:
  - `result_id`: UUID string
  - `metric_code`: string
  - `protocol_code`: string (`M9-P1-ENV-STATS`, `M9-P2-O2-DEPLETION`, `M9-P3-AIRFLOW-STEADY`, `M9-P4-FUEL-REGIMES`)
  - `canonical_name`: string
  - `result_kind`: string (`numeric`, `text`, `artifact`)
  - `numeric_value`: Decimal string or `None`
  - `unit`: string or `None`
  - `unit_status`: string (`known`, `unknown`, `not_applicable`)
  - `sample_size`: integer
  - `parameters`: JSON dictionary
  - `uncertainty`: JSON dictionary (order-statistic 95% CIs, IQRs)
  - `seal`: Dictionary with `seal_id`, `seal_version`, `member_digest`, `sealed_by`, `sealed_at`

### 2.2 Validation Rules & Edge Cases

| Scenario | Input Tested | Expected Outcome | Actual Result | Verification Status |
| :--- | :--- | :--- | :--- | :--- |
| **Valid Metric Code** | `metric_code="ambient_initial_o2_median"` | Returns sealed M9 result with 95% CI and seal metadata | Returned 1 sealed result with valid SHA-256 seal | **PASS** |
| **Invalid Metric Code** | `metric_code="fake_flame_speed_metric"` | Fast-fail with `INVALID_INPUT` and error listing valid metric codes | `INVALID_INPUT` returned; allowed metrics listed | **PASS** |
| **Invalid Protocol Code**| `protocol_code="M9-P99-UNKNOWN"` | Fast-fail with `INVALID_INPUT` and error listing valid protocols | `INVALID_INPUT` returned; allowed protocols listed | **PASS** |
| **Unsealed Result** | Result in `analytical_result` without `aggregate_seal` | Fast-fail with `INTEGRITY_FAILURE` | `INTEGRITY_FAILURE` returned; unsealed result detected | **PASS** |
| **Malformed Seal Digest**| `member_digest` with length $\ne 64$ | Fast-fail with `INTEGRITY_FAILURE` | `INTEGRITY_FAILURE` returned; invalid digest rejected | **PASS** |
| **Empty Results** | Metric not present in target investigation | Safe completion with `NO_RESULTS` | `NO_RESULTS` returned with empty data list | **PASS** |

---

## 3. Tool 2: `flare_query_observations`

### 3.1 Interface Contract
- **Input Parameters**:
  - `investigation`: `str` (default: `"PSI-25"`)
  - `test_number`: `str | None` (target test identifier)
  - `variable`: `str | None` (header or variable name filter)
  - `condition`: `str | None` (condition keyword filter)
  - `limit`: `int` (default: 50, maximum: 200)
- **Output Data Schema**: List of observation dictionaries containing:
  - `test_identifier`: string (e.g. `"test_01"`)
  - `source_record_number`: integer (CSV row number, 2..130)
  - `column_index`: integer (1-indexed CSV column ordinal)
  - `field_name`: string (e.g. `"Initial O2%"`, `"Air Display (cm/s)"`)
  - `raw_value`: string (unmodified raw CSV text)
  - `normalized_value`: string or `None` (exact Decimal string where available; **never coerced to 0**)
  - `unit`: string or `None`
  - `attribution`: string (`"experimental_measurement"`)
  - `quality_flags`: list of strings

### 3.2 Validation Rules & Edge Cases

| Scenario | Input Tested | Expected Outcome | Actual Result | Verification Status |
| :--- | :--- | :--- | :--- | :--- |
| **Filter by Test Identifier** | `test_number="test_01"` | Returns observations matching test 1 | Returned observations for `test_01` | **PASS** |
| **Filter by Variable Name** | `variable="Initial O2%"` | Returns observations matching initial oxygen column | Returned observations for `Initial O2%` | **PASS** |
| **Row Limit Capping** | `limit=1` | Limits returned records to 1 | Returned exactly 1 observation | **PASS** |
| **Row Limit Max Bounds** | `limit=9999` | Caps returned records at 200 | Capped at `MAX_OBSERVATION_LIMIT` (200) | **PASS** |
| **SQL Injection Attempt** | `test_number="test_01' OR 1=1; --"` | Parameterized SQL safely executes without injection | Sanitized execution; returned `NO_RESULTS` or nominal | **PASS** |
| **Missing Data Preservation**| Null/unannotated observation | Retains `None` / `null` without zero imputation | `normalized_value: None` preserved | **PASS** |
| **Empirical Attribution** | BASS-II observations | Tagged with `attribution: "experimental_measurement"` | 100% of rows marked `experimental_measurement` | **PASS** |

---

## 4. Tool 3: `flare_check_scientific_prohibition`

### 4.1 Interface Contract
- **Input Parameters**: `concept: str`
- **Output Data Schema**:
  - `concept`: string
  - `scope_status`: `ALLOWED` | `PROHIBITED` | `AMBIGUOUS` | `OUT_OF_SCOPE`
  - `is_prohibited`: boolean
  - `explanation`: string with authoritative physical rationale

### 4.2 Validation Rules & Edge Cases

| Concept Tested | Expected Scope | Execution Status | Authoritative Rationale Verified | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Biot Number ($Bi \ll 0.1$)** | `PROHIBITED` | `PROHIBITED` | Unverified thermal properties and heat transfer coefficients ($k$, $h$). | **PASS** |
| **Combustion Quotient ($RQ_{comb}$)**| `PROHIBITED` | `PROHIBITED` | Unaligned sensor lag and non-stoichiometric accumulation in unvented burns. | **PASS** |
| **Slab LOI Logistic Regression** | `PROHIBITED` | `PROHIBITED` | PMMA slab extinctions occurred under forced blowoff, not stagnant LOI equilibrium. | **PASS** |
| **Flame Spread Rate ($V_f$)** | `PROHIBITED` | `PROHIBITED` | Video tracking coordinates and camera timestamps not ingested in tabular data. | **PASS** |
| **Molar Consumption ($\Delta n_{O2}$)**| `PROHIBITED` | `PROHIBITED` | Chamber pressure logs and temperature transients uncalibrated. | **PASS** |
| **Cubic Airflow Polynomial** | `PROHIBITED` | `PROHIBITED` | Calibrated airflow velocity must strictly follow M9 quadratic nozzle curve. | **PASS** |
| **Lunar/Martian Extrapolation** | `PROHIBITED` | `PROHIBITED` | Extrapolation from ISS microgravity ($10^{-6}\,g$) to partial gravity unsupported. | **PASS** |
| **Fire-Risk Odds Ratios** | `PROHIBITED` | `PROHIBITED` | Sample size constraints and non-randomized convenience flight matrix. | **PASS** |
| **Ambient Initial Oxygen Query** | `ALLOWED` | `SUCCESS` | Complies with FLARE analytical scope. | **PASS** |
| **Missing Concept Parameter** | N/A | `INVALID_INPUT` | Parameter validation failure message returned. | **PASS** |

---

## 5. Tool 4: `flare_retrieve_documents`

### 5.1 Interface Contract
- **Input Parameters**: `query: str`, `evidence_type: str | None`, `top_k: int`
- **Output Status**: `NOT_IMPLEMENTED`
- **Validation**:
  - Returns structured `NOT_IMPLEMENTED` status.
  - Returns limitations explicitly referencing Milestone M10.4.
  - Confirms zero simulated or hallucinated text chunks were returned.
  - Status: **PASS**.
