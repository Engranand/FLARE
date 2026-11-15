# FLARE M6 — Remaining Risks & Operational Mitigation Plan

**Document Scope**: Post-Closure Risk Registry & Production Hardening Recommendations  
**Subject**: FLARE Milestone 6 Database Security Remediation & Ingestion Pipeline  
**Date**: November 14, 2026  
**Auditor**: Senior PostgreSQL Database Engineer & Security Specialist  

---

## 1. Executive Summary

While the Milestone 6 migration lineage repair successfully restored historical migration integrity and eliminated the client-side GUC validation bypass, five technical and operational risks remain that require documentation and planned mitigations prior to high-cadence production streaming.

None of these risks block immediate Milestone 8 development or batch ingestion on staging databases. However, they must be tracked in the operational runbook.

---

## 2. Risk Registry

### Risk 1: In-Flight Tracking Table Tuple Accumulation
- **Severity**: Medium  
- **Likelihood**: High (Guaranteed over time)  
- **Vulnerability / Root Cause**:  
  The trigger function `flare_sealing.check_parse()` inserts `(xact_id, parse_run_id)` into `flare_sealing.checked_parse` on each initial insert within a transaction. It does not perform a corresponding `DELETE` upon transaction commit. Consequently, every committed transaction that touches a `parse_run` permanently leaves a row in `checked_parse`.
- **Operational Impact**:  
  In batch ingestion (such as Milestone 8 BASS-II ingestion of 129 tests), this creates only 1 row. However, in continuous, 24/7 automated ingestion processing hundreds of thousands of transactions, `checked_parse` will accumulate millions of dead or obsolete tuples, consuming buffer pool cache and disk space.
- **Recommended Mitigation**:  
  Establish an automated operational maintenance job:
  ```sql
  -- Safe scheduled cleanup (e.g. daily cron):
  DELETE FROM flare_sealing.checked_parse 
  WHERE xact_id < pg_snapshot_xmin(pg_current_snapshot());
  ```
  Or a maintenance window truncate:
  ```sql
  TRUNCATE TABLE flare_sealing.checked_parse;
  ```

---

### Risk 2: Schema `public` Permissions in Legacy PostgreSQL Deployments
- **Severity**: Low  
- **Likelihood**: Low  
- **Vulnerability / Root Cause**:  
  `flare_sealing.check_parse()` defines `SET search_path = pg_catalog, flare_sealing, public`.  
  Inside `check_parse()`, it invokes `flare_sealing.parse_shape()`, which defines `SET search_path = pg_catalog, public` and queries `parse_run`, `source_record`, etc.  
  In PostgreSQL 15 and higher (such as the project's PostgreSQL 17 environment), `CREATE` on schema `public` is revoked from `PUBLIC` by default. However, in older PostgreSQL installations (PostgreSQL 14 and earlier) or improperly provisioned cloud instances where `CREATE` was explicitly granted to unprivileged database roles, an untrusted user could create a table or view in `public` that might interfere with queries.
- **Operational Impact**:  
  Potential schema namespace confusion or unexpected object resolution if unprivileged database roles are created with schema creation rights.
- **Recommended Mitigation**:  
  In production infrastructure provisioning scripts (Terraform/Ansible), enforce:
  ```sql
  REVOKE CREATE ON SCHEMA public FROM PUBLIC;
  REVOKE ALL ON SCHEMA flare_sealing FROM PUBLIC;
  GRANT USAGE ON SCHEMA flare_sealing TO flare_app;
  ```

---

### Risk 3: Accidental Downgrade of Migration 0008
- **Severity**: Medium  
- **Likelihood**: Very Low  
- **Vulnerability / Root Cause**:  
  Executing `alembic downgrade 0007_m45_n2` drops table `flare_sealing.checked_parse` and reverts `check_parse()` to the un-deduplicated M4.3 implementation.
- **Operational Impact**:  
  If downgraded accidentally in production, ingestion transactions would revert to running `parse_shape` on every single row insert ($O(N)$ overhead) or fail if unexpected schema dependencies exist.
- **Existing Mitigation in Code**:  
  Migration `0008_m6_security_remediation.py` includes an explicit safety interlock in `downgrade()`:
  ```python
  confirmed = context.config.attributes.get("allow_destructive_downgrade") is True
  if not confirmed and context.get_x_argument(as_dictionary=True).get("confirm_destructive_downgrade") != "yes":
      raise CommandError("Reverting M6 security remediation requires explicit confirmation")
  ```
  Any accidental `alembic downgrade` command will fail closed.

---

### Risk 4: Physical Streaming Replication to Read Replicas
- **Severity**: Low  
- **Likelihood**: Informational  
- **Vulnerability / Root Cause**:  
  `flare_sealing.checked_parse` is defined as an `UNLOGGED` table. Unlogged tables do not write to the PostgreSQL Write-Ahead Log (WAL).
- **Operational Impact**:  
  Table data is not replicated to physical streaming standby replicas (read replicas). The table structure (DDL) exists on replicas, but its data contents remain empty on replicas.
- **Assessment**:  
  This is by design and completely safe because `check_parse()` is a trigger that executes strictly on the primary database during `INSERT` transactions. Replicas are read-only and never execute ingestion write triggers.

---

### Risk 5: Monotonic Transaction Counter Wraparound
- **Severity**: Negligible  
- **Likelihood**: Mathematically Zero  
- **Vulnerability / Root Cause**:  
  Standard PostgreSQL transaction IDs (`xid`) wrap around after $2^{31}$ (2 billion) transactions, requiring vacuum freezes.
- **Assessment**:  
  `flare_sealing.checked_parse` explicitly uses `xact_id xid8` (64-bit integer from `pg_current_xact_id()`). A 64-bit counter will not wrap around for millions of years under maximum transactional load. There is zero wraparound risk for `xact_id`.

---

## 3. Summary Risk Matrix & Action Items

| Risk ID | Risk Summary | Severity | Status | Required Action / Owner |
| :--- | :--- | :--- | :--- | :--- |
| **R-01** | `checked_parse` row accumulation | Medium | Mitigated (By Design) | Add daily `DELETE WHERE xact_id < pg_snapshot_xmin(...)` to ops runbook. |
| **R-02** | Schema `public` `CREATE` rights | Low | Resolved in PG 17 | Ensure production Terraform scripts enforce `REVOKE CREATE ON SCHEMA public FROM PUBLIC`. |
| **R-03** | Accidental downgrade of 0008 | Medium | Hardened | Protected by `confirm_destructive_downgrade` guard in migration code. |
| **R-04** | Standby replication of UNLOGGED table | Low | Expected Behavior | Document in DBA architecture notes that `checked_parse` is primary-only. |
| **R-05** | Transaction ID wraparound | Negligible | Immune | Uses `xid8` (64-bit); no action required. |

---

## 4. Operational Sign-Off

The identified risks are standard PostgreSQL operational characteristics associated with `UNLOGGED` tables and `SECURITY DEFINER` trigger mechanics. None represent critical architectural vulnerabilities or blockers for Milestone 8 implementation.
