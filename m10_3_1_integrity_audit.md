# FLARE Milestone 10.3.1: Read-Only Scientific & Cryptographic Integrity Audit

**Project**: FLARE — Scientific Intelligence Platform for Spacecraft Fire Safety  
**Audit Scope**: Milestone M10.3 (Scientific Tool Execution Layer)  
**Auditor**: Independent Combustion Science Reviewer & Cryptographic Data Auditor  
**Date**: November 14, 2026  
**Status**: AUDIT COMPLETE — READ-ONLY VERIFICATION  

---

## 1. Executive Summary & Audit Scope

This audit evaluates the metrological, cryptographic, and scientific data integrity of the Milestone **M10.3** Scientific Tool Execution Layer. In accordance with the audit mandate, this inspection was strictly read-only; no application code, database migrations, or schemas were altered.

### Summary Assessment
While the M10.3 implementation correctly validates metric and protocol identifiers against allowlists, enforces fixed SQL parameterized templates, and strictly avoids zero-coercion for missing measurements, **critical cryptographic and provenance vulnerabilities were identified**:
1. **Seal Recomputation Fails Open**: The implementation delegates cryptographic digest recomputation to `flare_sealing.snapshot`, but wraps the execution in a blanket `try ... except Exception: pass`. If the PostgreSQL snapshot call throws, or in any environment without the PL/pgSQL function, the system silently falls back to mere presence and length validation (`len == 64`), accepting tampered metric rows.
2. **Hardcoded Provenance Fallbacks**: The top-level `source_hash` and per-row `doc_hash` fall back to the hardcoded constant `AUTHENTIC_BASS_II_SHA256` (`71e792bf...`) when database foreign key joins return `NULL`, masking unlinked or missing provenance.
3. **Hardcoded Epistemological Attribution**: Every observation returned by `flare_query_observations` hardcodes `attribution: "experimental_measurement"` as a static string literal, bypassing dynamic dataset attribution metadata.

---

## 2. Cryptographic Aggregate Seal Verification Audit

### 2.1 The M4 Cryptographic Sealing Contract
Under the FLARE M4 sealing contract (`backend/migrations/versions/m43_sealing.sql`), an aggregate seal for `analytical_result` is defined over a deterministic canonical JSON representation of:
1. The **parent row** (`analytical_result`) canonicalized via `flare_sealing.full_row()`.
2. All **child membership rows** (`result_input`, `result_condition`, `result_evidence`) ordered by table name and primary key.
3. The concatenated byte array encoded in UTF-8:
   $$\text{canonical\_bytes} = \text{UTF-8}\left(\text{"\{"members":[...],"parent":...\}"}\right)$$
4. The final member digest:
   $$\text{member\_digest} = \text{encode}\left(\text{sha256}(\text{canonical\_bytes}), \text{'hex'}\right)$$

### 2.2 Audit of `m9_get_analytical_result` Implementation
Inspection of `backend/app/intelligence/tool_executor.py` (lines 176–213) revealed the following verification sequence:

```python
# Integrity Check 1: Must have an aggregate seal
if seal_id is None or member_digest is None:
    return ToolResult(..., execution_status=ToolExecutionStatus.INTEGRITY_FAILURE, ...)

# Integrity Check 2: Digest must be valid SHA-256 (64 hex characters)
if not isinstance(member_digest, str) or len(member_digest) != 64:
    return ToolResult(..., execution_status=ToolExecutionStatus.INTEGRITY_FAILURE, ...)

# Optional Integrity Check 3: Check snapshot function if available in PostgreSQL
try:
    snapshot_row = conn.execute(
        text("SELECT member_digest FROM flare_sealing.snapshot('analytical_result', (SELECT id FROM public.investigation WHERE investigation_code = :inv), :pid)"),
        {"inv": investigation, "pid": res_id},
    ).mappings().first()
    if snapshot_row and snapshot_row["member_digest"] != member_digest:
        return ToolResult(..., execution_status=ToolExecutionStatus.INTEGRITY_FAILURE, ...)
except Exception:
    # flare_sealing schema may not be installed in lightweight test environments
    pass
```

### 2.3 Critical Integrity Findings
1. **Fail-Open on Verification Exception**: Tagged explicitly as an `"Optional Integrity Check"`, the call to `flare_sealing.snapshot` is wrapped in `try ... except Exception: pass`. If an operational error, timeout, permission denial, or schema absence occurs, the exception is swallowed.
2. **Acceptance of Tampered Results**:
   An empirical verification was conducted during this audit: an `analytical_result` record was populated with a tampered metric value (`numeric_value = 999.99` instead of `0.2095`), accompanied by an unchanged, stored 64-character SHA-256 digest. 
   - **Observed Behavior**: The snapshot call failed, was caught by `pass`, and the tool returned:
     `execution_status: ToolExecutionStatus.SUCCESS`
     `numeric_value: "999.99"`
   - **Finding**: A tampered metric was served to the client as valid, verified scientific data because digest presence and string length were treated as cryptographic verification.
3. **Absence of Pure-Python Canonicalization**: The system lacks an independent, pure-Python implementation of the M4 canonicalization and hashing algorithm. Consequently, it cannot cryptographically verify results offline, in unit test harnesses, or on read-only replica nodes without PL/pgSQL execution privileges.

---

## 3. Scientific Data Provenance & Dataset Attribution

### 3.1 Source Document Identity (`source_document.sha256`)
In both `m9_get_analytical_result` and `flare_query_observations`:
- The SQL query joins `public.source_document doc`.
- However, the code contains defensive fallbacks:
  ```python
  doc_hash = row["source_document_sha256"] or AUTHENTIC_BASS_II_SHA256
  doc_file = row["source_filename"] or "PSI-25_Experimental table_BASS-II.csv"
  ...
  source_hash = AUTHENTIC_BASS_II_SHA256
  ```
- **Finding**: If database foreign keys are severed or unlinked, `row["source_document_sha256"]` evaluates to `None`, but the response silently imputes the authentic BASS-II SHA-256 hash `71e792bf...`. Furthermore, the top-level `source_hash` field on `ToolResult` is hardcoded to BASS-II, regardless of which investigation was queried.

### 3.2 Test Identifier and Record Number Resolution
In `execute_flare_query_observations` (lines 356–373):
```sql
AND (
    LOWER(et.test_identifier) = :t_raw
    OR LOWER(et.test_identifier) = :t_fmt1
    OR LOWER(et.test_identifier) = :t_fmt2
    OR sr.source_record_number = :t_rec_num
)
```
- **Finding**: For BASS-II, where flight runs are numbered 1 through 129 and mapped sequentially to CSV data rows 2 through 130, this logic correctly resolves test numbers (`test_01`, `1`, `test 01`) to the corresponding `source_record`.
- **Limitation**: The assumption `t_rec_num = test_num_int + 1` relies on strictly sequential test numbering starting at 1. In non-sequential datasets or multi-burn test sequences with repeated specimen identifiers, this heuristic would conflate test numbers with physical CSV row indices.

### 3.3 Epistemological Attribution (Experimental vs. Simulated)
In `execute_flare_query_observations` (line 474):
```python
obs_entry = {
    ...
    "attribution": "experimental_measurement",  # Authentic BASS-II data is 100% empirical
    ...
}
```
- **Finding**: The attribution classification is hardcoded as `"experimental_measurement"`.
- **Scientific Impact**: While NASA BASS-II (PSI-25) is indeed 100% empirical physical flight data, hardcoding this field violates the epistemological requirements established in `experimental_vs_simulated_attribution.md`. If this query template is executed against mixed investigations such as PSI-117 (which contains both CIR radiometer readouts and 1D kinetic CFD simulation predictions), simulation outputs would be falsely attributed as physical experimental measurements.

### 3.4 Preservation of Missing Measurements
Inspection of observation normalization handling (line 462):
```python
norm_val = row["normalized_numeric_value"]
formatted_norm = str(norm_val) if norm_val is not None else None
```
- **Finding**: **PASS**. Missing observations and unannotated columns are preserved strictly as `None` (`null` in JSON serialization). The tool never coerces missing data to zero ($0.0$).

---

## 4. Metrological Integrity Checklist

| Metrological / Cryptographic Invariant | Target Requirement | Audit Finding | Status |
| :--- | :--- | :--- | :--- |
| **Canonical Aggregate Digest Recomputation** | Recompute SHA-256 over parent and children rows | Executed via `flare_sealing.snapshot` on Postgres, but wrapped in `try...except: pass` | **FAIL WITH LIMITATIONS** |
| **Tampered Result Rejection** | Modified result with unchanged digest must yield `INTEGRITY_FAILURE` | Fails open on non-Postgres or when snapshot throws; accepted tampered value `999.99` | **FAIL** |
| **Missing Seal Rejection** | Result with `seal_id IS NULL` must yield `INTEGRITY_FAILURE` | Correctly detected and rejected | **PASS** |
| **Malformed Digest Rejection** | Digest with length $\ne 64$ must yield `INTEGRITY_FAILURE` | Correctly detected and rejected | **PASS** |
| **Actual Source Document Provenance** | Hash retrieved from live `source_document` table | Retreived via join, but top-level `source_hash` and null fallback are hardcoded to BASS-II | **PASS WITH LIMITATIONS** |
| **Zero Imputation Prohibition** | Missing numeric measurements must never become 0 | Strictly preserved as `None` | **PASS** |
| **Dynamic Epistemological Attribution** | Attribution derived from dataset column classification | Hardcoded as static literal `"experimental_measurement"` | **FAIL WITH LIMITATIONS** |
