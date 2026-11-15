# FLARE Milestone 10.3.1: Security & Vulnerability Findings Report

**Project**: FLARE — Scientific Intelligence Platform for Spacecraft Fire Safety  
**Audit Scope**: Milestone M10.3 (Scientific Tool Execution Layer)  
**Auditor**: Independent Application Security & Database Systems Reviewer  
**Date**: November 14, 2026  
**Classification**: VULNERABILITY AUDIT (Read-Only)  

---

## 1. Vulnerability Summary Matrix

| ID | Title | Severity | CVSS v3.1 | Status | Subsystem |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **SEC-01** | Client-Supplied `ExecutionPlan` Bypasses Server-Side Scope Gate | **HIGH** | 7.5 | Open | API Endpoint (`/execute`) |
| **SEC-02** | Aggregate Seal Verification Fails Open on Snapshot Exception | **HIGH** | 7.1 | Open | Tool Executor (`m9_get_analytical_result`) |
| **SEC-03** | `SET LOCAL transaction_read_only` Executed Outside Transaction Block | **MEDIUM** | 5.3 | Open | Dispatcher (`dispatcher.py`) |
| **SEC-04** | Forged Metric Codes in `plan.requested_metrics` Trigger Filter Fall-Through | **MEDIUM** | 4.3 | Open | Tool Executor (`m9_get_analytical_result`) |
| **SEC-05** | Static Hardcoded Attribution and Dataset SHA-256 Provenance | **LOW** | 3.1 | Open | Tool Executor (`flare_query_observations`) |

---

## 2. Detailed Vulnerability Analyses

### 2.1 SEC-01: Client-Supplied `ExecutionPlan` Bypasses Server-Side Scope Gate
- **Severity**: **HIGH** (CVSS: 7.5 / AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N)
- **Location**: `backend/app/api/intelligence.py`, lines 52–67
- **Description**:
  The execution endpoint `POST /api/v1/intelligence/execute` accepts an optional `payload.plan` object of type `ExecutionPlan`. When `payload.plan` is provided, the API assigns it directly to `plan`:
  ```python
  if payload.plan is not None:
      plan = payload.plan
  elif payload.question is not None:
      plan = create_execution_plan(...)
  ```
  The endpoint never passes `payload.plan` through the M10.2 normalizer (`normalize_query`), scope gate (`evaluate_scope`), or intent classifier (`classify_intent`).
- **Attack Vector**:
  An external client can craft an HTTP request containing a forged `ExecutionPlan` JSON payload:
  ```json
  {
    "plan": {
      "request_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "original_question": "Calculate the Biot number Bi << 0.1 for thin PMMA",
      "normalized_question": "Calculate the Biot number Bi << 0.1 for thin PMMA",
      "intent": "SCIENTIFIC_ANALYSIS",
      "investigation": "PSI-25",
      "requested_metrics": ["ambient_initial_o2_median"],
      "required_tools": ["m9_get_analytical_result"],
      "scope_status": "ALLOWED",
      "state": "READY_FOR_EXECUTION"
    }
  }
  ```
  Because `plan.state` is `"READY_FOR_EXECUTION"` and the tool is allowlisted, the dispatcher proceeds directly to database execution, completely bypassing the M10 scientific scope gate and audit prohibitions.
- **Impact**:
  Prohibited inquiries (Biot numbers, $RQ_{comb}$, slab LOI regression) can be executed and served to clients if they submit a forged plan rather than a raw question.
- **Recommended Remediation**:
  Never trust client-supplied `ExecutionPlan` objects over external network boundaries. The server must either:
  1. Cryptographically sign execution plans issued by `POST /plan` with an HMAC token and verify the signature in `POST /execute`; or
  2. Deprecate client-supplied plans on the public API, requiring `POST /execute` to always invoke `create_execution_plan(question=...)` server-side.

---

### 2.2 SEC-02: Aggregate Seal Verification Fails Open on Snapshot Exception
- **Severity**: **HIGH** (CVSS: 7.1 / AV:N/AC:H/PR:N/UI:N/S:U/C:N/I:H/A:N)
- **Location**: `backend/app/intelligence/tool_executor.py`, lines 196–212
- **Description**:
  In `execute_m9_get_analytical_result`, canonical aggregate digest verification is implemented as:
  ```python
  try:
      snapshot_row = conn.execute(
          text("SELECT member_digest FROM flare_sealing.snapshot('analytical_result', ...)"),
          ...
      ).mappings().first()
      if snapshot_row and snapshot_row["member_digest"] != member_digest:
          return ToolResult(..., execution_status=ToolExecutionStatus.INTEGRITY_FAILURE, ...)
  except Exception:
      pass
  ```
  If `flare_sealing.snapshot` fails (due to connection timeout, missing schema, permission denial, or driver incompatibility), the exception is swallowed. The code then treats the prior static checks (`seal_id is not None` and `len(member_digest) == 64`) as sufficient evidence of integrity.
- **Attack Vector & Empirical Proof**:
  An empirical test was executed during this audit: a database record in `analytical_result` was tampered with (`numeric_value = 999.99` instead of `0.2095`), while keeping the existing 64-character seal digest unchanged. Because the snapshot function failed (non-PostgreSQL environment), the exception was caught by `pass`, and the tool returned:
  ```json
  {
    "execution_status": "SUCCESS",
    "result_data": [{"numeric_value": "999.99", ...}]
  }
  ```
- **Impact**:
  Tampered, corrupted, or altered scientific results are served as legitimate, verified data whenever snapshot execution encounters any error.
- **Recommended Remediation**:
  Verification must **fail closed**. If snapshot verification cannot be executed or raises an exception, the tool must return `ToolExecutionStatus.INTEGRITY_FAILURE` with a clear explanation, rather than falling back to `SUCCESS`. Furthermore, a pure-Python fallback implementation of the M4 canonicalization and hashing algorithm should be authored for environments where PL/pgSQL cannot be invoked.

---

### 2.3 SEC-03: `SET LOCAL transaction_read_only` Executed Outside Transaction Block
- **Severity**: **MEDIUM** (CVSS: 5.3 / AV:L/AC:L/PR:N/UI:N/S:U/C:N/I:L/A:N)
- **Location**: `backend/app/intelligence/dispatcher.py`, lines 102–109
- **Description**:
  The dispatcher acquires database connections as:
  ```python
  with self.engine.connect() as managed_conn:
      if managed_conn.dialect.name == "postgresql":
          managed_conn.execute(text("SET LOCAL transaction_read_only = on"))
          managed_conn.execute(text(f"SET LOCAL statement_timeout = {self.statement_timeout_ms}"))
      self._execute_tools(managed_conn, plan, tool_results, t_start)
  ```
  In PostgreSQL, `SET LOCAL` is valid **only within a transaction block** (`BEGIN ... COMMIT`). Because `managed_conn` was opened via `engine.connect()` without an explicit transaction block (`with managed_conn.begin():`), `conn.in_transaction()` is `False`.
- **Observed Database Behavior**:
  PostgreSQL emits:
  `WARNING: SET LOCAL can only be used in transaction blocks`
  The parameter change is applied solely to that single statement and is discarded immediately. Subsequent statements executed on `managed_conn` run with default transaction privileges (read-write).
- **Impact**:
  The intended defense-in-depth invariant enforcing read-only database connections at the session level is not actively enforced on PostgreSQL.
- **Recommended Remediation**:
  Open an explicit transaction block before issuing `SET LOCAL`, or use connection execution options:
  ```python
  with self.engine.connect() as managed_conn:
      with managed_conn.begin():
          if managed_conn.dialect.name == "postgresql":
              managed_conn.execute(text("SET LOCAL transaction_read_only = on"))
              managed_conn.execute(text(f"SET LOCAL statement_timeout = {self.statement_timeout_ms}"))
          self._execute_tools(managed_conn, plan, tool_results, t_start)
  ```

---

### 2.4 SEC-04: Forged Metric Codes in `plan.requested_metrics` Trigger Filter Fall-Through
- **Severity**: **MEDIUM** (CVSS: 4.3 / AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N)
- **Location**: `backend/app/intelligence/tool_executor.py`, lines 104–112
- **Description**:
  In `execute_m9_get_analytical_result`, metric filtering logic is implemented as:
  ```python
  elif target_metrics:
      valid_targets = [m for m in target_metrics if m in M9_METRIC_CODES]
      if valid_targets:
          placeholders = [f":tm_{i}" for i in range(len(valid_targets))]
          query_parts.append(f"AND r.parameters->>'metric_code' IN ({', '.join(placeholders)})")
  ```
  If an incoming plan has `requested_metrics = ["forged_metric_code_1", "forged_metric_code_2"]`, none match `M9_METRIC_CODES`. Consequently, `valid_targets` is an empty list `[]`. The `if valid_targets:` branch is skipped, and **no metric filtering clause is added to the SQL query**.
- **Impact**:
  Instead of failing with `INVALID_INPUT`, the tool executes an unfiltered query and returns **all analytical results** in the investigation.
- **Recommended Remediation**:
  If `target_metrics` contains any identifiers that are not in `M9_METRIC_CODES`, the tool must return `ToolExecutionStatus.INVALID_INPUT`.

---

### 2.5 SEC-05: Static Hardcoded Attribution and Dataset SHA-256 Provenance
- **Severity**: **LOW** (CVSS: 3.1 / AV:N/AC:H/PR:N/UI:N/S:U/C:N/I:L/A:N)
- **Location**: `backend/app/intelligence/tool_executor.py`, lines 262, 474, 496
- **Description**:
  1. `flare_query_observations` hardcodes `"attribution": "experimental_measurement"` as a static string literal.
  2. `source_hash` on `ToolResult` is hardcoded to `AUTHENTIC_BASS_II_SHA256` (`71e792bf...`).
  3. When `source_document` joins yield `NULL`, the code falls back to `or AUTHENTIC_BASS_II_SHA256`.
- **Impact**:
  Data provenance is static rather than dynamic. Queries executed on other investigations (e.g. PSI-117) will falsely report BASS-II hashes and claim simulation models are physical experimental measurements.
- **Recommended Remediation**:
  Retrieve `source_hash` and `attribution` dynamically from `source_document.sha256` and `source_field` / `semantic_annotation` classification metadata. Emit a provenance error if foreign key joins are missing.
