# FLARE Milestone 10.3.2: Security & Integrity Remediation Report

**Project**: FLARE — Scientific Intelligence Platform for Spacecraft Fire Safety  
**Milestone**: M10.3.2 — Security Hardening & Cryptographic Seal Verification Remediation  
**Date**: November 14, 2026  
**Status**: APPROVED & FULLY REMEDIATED  
**Classification**: ENGINEERING REMEDIATION REPORT  

---

## 1. Executive Summary

During the independent Milestone M10.3.1 audit, five security and data integrity vulnerabilities were identified in the Scientific Tool Execution Layer:
- **SEC-01 (High)**: Client-supplied `ExecutionPlan` bypassed server-side scope gating on `POST /api/v1/intelligence/execute`.
- **SEC-02 (High)**: Aggregate seal verification failed open on snapshot recomputation exceptions.
- **SEC-03 (Medium)**: `SET LOCAL transaction_read_only = on` was executed outside an explicit transaction block.
- **SEC-04 (Medium)**: Forged metric codes in `plan.requested_metrics` triggered filter fall-through.
- **SEC-05 (Low)**: Static hardcoded attribution and dataset SHA-256 provenance fallbacks.

Milestone M10.3.2 has comprehensively resolved all five findings, verified full regression safety across 111 unit tests, and introduced an end-to-end integration test suite executed against live, isolated PostgreSQL 17 clusters (`C:\Program Files\PostgreSQL\17\bin`).

---

## 2. Vulnerability Remediation Summary Matrix

| ID | Title | Original Severity | Status | Remediated Subsystem | Verification Test |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **SEC-01** | Client-Supplied `ExecutionPlan` Bypasses Scope Gate | **HIGH** | **CLOSED** | `app/api/intelligence.py` & `dispatcher.py` | `test_sec01_client_supplied_forged_plan_is_reconstructed_and_rejected`, `test_pg_sec01_client_supplied_forged_plan_gated` |
| **SEC-02** | Aggregate Seal Verification Fails Open on Exception | **HIGH** | **CLOSED** | `app/intelligence/tool_executor.py` | `test_sec02_tampered_snapshot_digest_triggers_integrity_failure`, `test_pg_sec02_tampered_metric_value_fails_closed`, `test_pg_sec02_tampered_seal_digest_fails_closed` |
| **SEC-03** | `SET LOCAL` Executed Outside Transaction Block | **MEDIUM** | **CLOSED** | `app/intelligence/dispatcher.py` | `test_pg_sec03_read_only_transaction_enforcement` |
| **SEC-04** | Forged Metric Codes Trigger Filter Fall-Through | **MEDIUM** | **CLOSED** | `app/intelligence/tool_executor.py` | `test_sec04_forged_metric_codes_in_target_metrics_rejected`, `test_pg_sec04_forged_metric_codes_rejected` |
| **SEC-05** | Static Hardcoded Attribution & Dataset Provenance | **LOW** | **CLOSED** | `app/intelligence/tool_executor.py` | `test_sec05_dynamic_epistemic_attribution`, `test_pg_sec05_dynamic_source_provenance_and_attribution` |

---

## 3. Deep-Dive Remediation Analyses

### 3.1 SEC-01: Execution Plan Trust & Server-Side Plan Reconstruction
- **Root Cause**: The execution endpoint `POST /api/v1/intelligence/execute` accepted a client-provided `ExecutionPlan` without re-running normalization, scope evaluation, or intent classification.
- **Remediation**:
  1. Updated `app/api/intelligence.py`: Regardless of whether `payload.plan` or `payload.question` is submitted, the server extracts `question_text` and invokes `create_execution_plan(question=question_text, ...)` server-side.
  2. The server-reconstructed plan is authoritative. If the question involves prohibited concepts (e.g. Biot number calculation, $RQ_{comb}$, slab LOI regression), the server plan marks `state = QueryState.ABSTAINED` and `scope_status = ScopeStatusEnum.PROHIBITED`.
  3. Defense-in-depth: If `plan.state == QueryState.ABSTAINED` or `plan.scope_status in (PROHIBITED, OUT_OF_SCOPE)`, the dispatcher short-circuits immediately, returning `ToolExecutionStatus.PROHIBITED` with zero tool dispatches.

### 3.2 SEC-02: Cryptographic Seal Verification & Fail-Closed Invariants
- **Root Cause**: In `tool_executor.py`, calls to `flare_sealing.snapshot('analytical_result', ...)` were wrapped in `try ... except Exception: pass`, allowing verification to fail open if the snapshot query failed.
- **Remediation**:
  1. Removed `try ... except Exception: pass`.
  2. On PostgreSQL, `flare_sealing.snapshot` is called to recompute canonical member digests. If the function raises ANY exception, or if `snapshot_row["member_digest"] != member_digest`, the execution immediately fails closed with `ToolExecutionStatus.INTEGRITY_FAILURE`.
  3. Added deterministic mapping for all 20 M9 metric codes (`M9_METRIC_UUIDS`) to enable direct primary-key lookups against `public.analytical_result`.
  4. Added mock snapshot verification table support for SQLite test harnesses.

### 3.3 SEC-03: Read-Only Transaction Enforcement
- **Root Cause**: `SET LOCAL transaction_read_only = on` was executed without an explicit transaction block (`managed_conn.begin()`), causing PostgreSQL to emit a warning and discard the read-only flag.
- **Remediation**:
  1. Updated `ToolDispatcher.dispatch_plan` in `app/intelligence/dispatcher.py` to wrap connection usage in `with managed_conn.begin():`.
  2. Inside the active transaction block, `SET LOCAL transaction_read_only = on` and `SET LOCAL statement_timeout = :timeout` are executed.
  3. Verified on live PostgreSQL 17 that any subsequent write mutation (`INSERT`, `UPDATE`, `DELETE`) fails with PostgreSQL error `25006` (`read_only_sql_transaction`).

### 3.4 SEC-04: Metric Code Allowlisting & Filter Fall-Through Prevention
- **Root Cause**: When `target_metrics` was provided with invalid or forged codes, filtering fell through to an empty `valid_targets` list, returning all analytical results unfiltered.
- **Remediation**:
  1. In `execute_m9_get_analytical_result`, explicit validation ensures all metrics in `target_metrics` exist in `M9_METRIC_CODES`.
  2. If any metric is unknown, `ToolExecutionStatus.INVALID_INPUT` is returned immediately without executing database queries.

### 3.5 SEC-05: Dynamic Source Provenance & Epistemic Attribution
- **Root Cause**: `flare_query_observations` hardcoded `"attribution": "experimental_measurement"` and `source_hash = AUTHENTIC_BASS_II_SHA256`.
- **Remediation**:
  1. Attribution is derived dynamically from `parser_classification`, `source_value_kind`, and source document filename metadata.
  2. Distinguishes `numerical_simulation`, `derived_quantity`, `reference_value`, and `experimental_measurement`.
  3. Any unknown or unverified classification resolves strictly to `UNRESOLVED` (never defaults to experimental).
  4. `source_hash` and evidence references are populated dynamically from `source_document.sha256` joins.

---

## 4. Codebase Modifications Catalog

1. `backend/app/api/intelligence.py`:
   - Enforced server-side plan reconstruction from question text.
   - Prevented client-supplied `ExecutionPlan` from bypassing scope validation.
2. `backend/app/intelligence/dispatcher.py`:
   - Wrapped tool execution in explicit transaction blocks (`with managed_conn.begin():`).
   - Added early abstention short-circuiting for prohibited queries.
   - Enforced `SET LOCAL transaction_read_only = on` and statement timeout.
3. `backend/app/intelligence/tool_executor.py`:
   - Implemented fail-closed cryptographic snapshot verification via `flare_sealing.snapshot`.
   - Added `M9_METRIC_UUIDS`, `M9_UUID_TO_METRIC`, `M9_METRIC_TO_NAME`, and `M9_METRIC_SAMPLE_SIZES`.
   - Added strict validation for `target_metrics` returning `INVALID_INPUT` on invalid codes.
   - Implemented dynamic epistemic attribution and dynamic source document provenance.
4. `backend/tests/unit/test_m10_3_tool_execution.py`:
   - Added `TestM1032Remediations` covering SEC-01, SEC-02, SEC-04, and SEC-05 (4 new tests, 28 total passing).
5. `backend/tests/integration/test_m10_3_execution.py`:
   - Authored new integration test suite executing 8 tests against live PostgreSQL 17 clusters.
