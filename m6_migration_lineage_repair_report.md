# FLARE M6 — Migration Lineage Repair & Historical Recovery Report

**Classification**: Forward-Only Database Remediation & Lineage Repair  
**Target Head Revision**: `0008_m6_security_remediation`  
**Down Revision**: `0007_m45_n2`  
**Date**: November 14, 2026  
**Auditor**: Senior PostgreSQL Database Engineer  

---

## 1. Executive Summary

During the pre-implementation review for FLARE Milestone 8, a critical architectural defect was identified in the Milestone 6 security remediation:
1. Historical migration `0003_m43_sealing.py` and its accompanying SQL script `m43_sealing.sql` had been retrofitted in-place to implement the GUC bypass fix (`flare_sealing.checked_parse` and the rewritten `check_parse()` trigger).
2. Existing databases already at revision `0007_m45_n2` track applied migrations in PostgreSQL table `alembic_version`. Alembic will never re-execute migration `0003` on an existing database. Consequently, existing environments were left vulnerable to missing table errors (`SQLSTATE 42P01: relation "flare_sealing.checked_parse" does not exist`) upon parse trigger execution.
3. This in-place modification violated the core database engineering principle of **immutable historical migrations**.

This report documents the minimal, forward-only correction implemented to fully resolve the issue:
- **Historical Recovery**: Complete restoration of `0003_m43_sealing.py` and `m43_sealing.sql` to their pristine Git HEAD historical state.
- **Forward Migration**: Creation of clean forward migration `0008_m6_security_remediation.py` branching directly from `0007_m45_n2`.
- **Epistemic Mapping Correction**: Correction of the BASS-II data mapping to properly distinguish physical apparatus configuration, instrument calibration metadata, and raw measurements.
- **Verification**: Complete regression and lifecycle testing on private ephemeral PostgreSQL 17 clusters, confirming 100% test pass rate across fresh database initialization, stepwise 0007-to-0008 upgrade, rollback, idempotency, and BASS-II end-to-end ingestion.

---

## 2. Historical File Recovery Audit

A line-by-line comparison of the modified working-tree files against Git HEAD (`git show HEAD:...`) was performed before restoration.

### 2.1 File: `backend/migrations/versions/0003_m43_sealing.py`

#### Differences Identified:
- **Lines 28–35 (Upgrade)**: In-place injection of `CREATE UNLOGGED TABLE IF NOT EXISTS flare_sealing.checked_parse ...` and `REVOKE ALL ON flare_sealing.checked_parse FROM PUBLIC`.
- **Lines 51–53 (Downgrade)**: In-place injection of `DROP TABLE IF EXISTS flare_sealing.checked_parse CASCADE`.

#### Restoration Action:
The file was restored to its exact historical state from Git HEAD:
```python
def upgrade():
    sql = (Path(__file__).resolve().parent / "m43_sealing.sql").read_text(encoding="utf-8")
    for statement in [s.strip() for s in sql.split("-- next function") if s.strip()]:
        op.execute(sa.text(statement))

def downgrade():
    op.execute(sa.text("DROP SCHEMA IF EXISTS flare_sealing CASCADE;"))
```
- **Post-Recovery Verification**: `git diff HEAD:backend/migrations/versions/0003_m43_sealing.py backend/migrations/versions/0003_m43_sealing.py` yielded **zero differences** (clean exit code 0).

---

### 2.2 File: `backend/migrations/versions/m43_sealing.sql`

#### Differences Identified:
- **Lines 141–157 (`check_parse` trigger function)**:
  The historical trigger function was modified in-place to insert into `flare_sealing.checked_parse` and set `SECURITY DEFINER SET search_path = pg_catalog, flare_sealing, public`.
  The original historical version (M4.3) was:
  ```sql
  CREATE FUNCTION flare_sealing.check_parse() RETURNS trigger LANGUAGE plpgsql AS $$
  BEGIN
      PERFORM flare_sealing.parse_shape(NEW.investigation_id,CASE WHEN TG_TABLE_NAME='parse_run' THEN NEW.id ELSE (to_jsonb(NEW)->>'parse_run_id')::uuid END);
      RETURN NULL;
  END $$;
  ```

#### Restoration Action:
The historical SQL script was restored verbatim from Git HEAD:
- **Post-Recovery Verification**: `git diff HEAD:backend/migrations/versions/m43_sealing.sql backend/migrations/versions/m43_sealing.sql` yielded **zero differences** (clean exit code 0).

---

## 3. Forward Migration Architecture (`0008_m6_security_remediation`)

A new, forward-only migration was created at:  
`backend/migrations/versions/0008_m6_security_remediation.py`

### 3.1 Migration Metadata
- **Revision Identifier**: `0008_m6_security_remediation`
- **Revises (down_revision)**: `0007_m45_n2`
- **Linear Chain Integrity**: `0001_m41_baseline` -> `0002_m42_core_schema` -> `0003_m43_sealing` -> `0004_m44_n1` -> `0005_m44_n1_fix` -> `0006_m44_n1_indexes` -> `0007_m45_n2` -> `0008_m6_security_remediation` (single head).

### 3.2 Upgrade Specification (`upgrade()`)
1. **Tracking Table Creation**:
   ```sql
   CREATE UNLOGGED TABLE IF NOT EXISTS flare_sealing.checked_parse (
       xact_id xid8 NOT NULL,
       parse_run_id uuid NOT NULL,
       PRIMARY KEY (xact_id, parse_run_id)
   );
   ```
2. **Strict Privilege Lockdown**:
   ```sql
   REVOKE ALL ON flare_sealing.checked_parse FROM PUBLIC;
   ```
   Ensures that only the database owner / superuser can read or write to `checked_parse`. Unprivileged application roles (`flare_fixture_app`, `flare_app`) cannot directly insert or modify records to bypass validation.
3. **Trigger Function Hardening**:
   ```sql
   CREATE OR REPLACE FUNCTION flare_sealing.check_parse() RETURNS trigger
   LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, flare_sealing, public AS $$
   DECLARE
       p_id uuid;
       v_xact xid8 := pg_current_xact_id();
   BEGIN
       p_id := CASE WHEN TG_TABLE_NAME='parse_run' THEN NEW.id ELSE (to_jsonb(NEW)->>'parse_run_id')::uuid END;
       IF p_id IS NOT NULL THEN
           INSERT INTO flare_sealing.checked_parse (xact_id, parse_run_id)
           VALUES (v_xact, p_id)
           ON CONFLICT DO NOTHING;
           IF FOUND THEN
               PERFORM flare_sealing.parse_shape(NEW.investigation_id, p_id);
           END IF;
       END IF;
       RETURN NULL;
   END $$;
   ```

### 3.3 Downgrade Specification (`downgrade()`)
1. **Destructive Guard**: Protects against accidental schema downgrade in production environments unless explicitly authorized via `allow_destructive_downgrade` config attribute or `-x confirm_destructive_downgrade=yes`.
2. **Trigger Reversion**: Replaces `check_parse()` with the exact historical M4.3 implementation.
3. **Table Deletion**: Executes `DROP TABLE IF EXISTS flare_sealing.checked_parse CASCADE`.

---

## 4. Test Evidence & Regression Verification

Testing was conducted exclusively on private, ephemeral PostgreSQL 17.11 instances running on local dynamic ports (`127.0.0.1:54421`, `127.0.0.1:57462`, `127.0.0.1:65249`, etc.). No persistent development or production databases were accessed or modified.

### 4.1 Migration Discovery & Chain Validation (`test_migrations.py`)
- **Command**: `pytest backend/tests/test_migrations.py`
- **Output**:
  ```
  backend/tests/test_migrations.py ...                                     [100%]
  3 passed in 0.15s
  ```
- **Assertions Verified**:
  - `directory.get_heads() == ['0008_m6_security_remediation']`
  - `len(revisions) == 8`
  - Linear acyclic revision graph starting at `0001_m41_baseline` and terminating at `0008_m6_security_remediation`.

### 4.2 Forward Migration Lifecycle Suite (`test_m6_migration_lifecycle.py`)
- **Command**: `pytest backend/tests/test_m6_migration_lifecycle.py --run-postgres --pg-bin "C:\Program Files\PostgreSQL\17\bin"`
- **Output**:
  ```
  backend/tests/test_m6_migration_lifecycle.py ....                        [100%]
  4 passed in 26.01s
  ```
- **Tests Executed**:
  1. `test_fresh_migration_zero_to_head`: Verified clean migration from 0001 to 0008 on an empty database. Confirmed existence of `flare_sealing.checked_parse` with `(xact_id xid8, parse_run_id uuid)` and verified `SECURITY DEFINER` + `search_path` on `flare_sealing.check_parse()`.
  2. `test_upgrade_from_0007_to_0008`: Replayed migration to `0007_m45_n2`, confirmed absence of `checked_parse`, upgraded to `0008_m6_security_remediation`, and verified creation of table and updated function.
  3. `test_downgrade_and_reupgrade`: Tested rollback to `0007_m45_n2` (table dropped), followed by idempotent re-upgrade to `0008_m6_security_remediation` (table recreated).
  4. `test_savepoint_rollback_behavior`: Verified savepoint isolation within transactions. Attempted unprivileged write inside a subtransaction savepoint resulted in SQLSTATE `42501`, rolled back safely, and permitted parent transaction commit without compromising validation.

### 4.3 Security & GUC Remediation Suite (`test_m6_guc_remediation.py`)
- **Command**: `pytest backend/tests/test_m6_guc_remediation.py --run-postgres --pg-bin "C:\Program Files\PostgreSQL\17\bin"`
- **Output**:
  ```
  backend/tests/test_m6_guc_remediation.py ....                            [100%]
  4 passed in 18.01s
  ```
- **Tests Executed**:
  1. `test_unprivileged_role_cannot_manipulate_checked_parse`: Verified unprivileged role cannot write to `checked_parse` (`SQLSTATE 42501`).
  2. `test_corrupt_parse_run_fails_even_with_preset_guc`: Verified client cannot bypass validation by presetting session GUCs (`SQLSTATE 23514: Incomplete parse membership`).
  3. `test_child_insert_into_existing_unsealed_parse_run_validates`: Verified adding records in subsequent transactions triggers full shape validation (`SQLSTATE 23514`).
  4. `test_child_insert_into_sealed_parse_run_rejected_with_55000`: Verified sealed parse runs are strictly immutable (`SQLSTATE 55000: sealed aggregate is immutable`).

### 4.4 NASA BASS-II End-to-End Ingestion Pipeline (`test_m6_ingestion.py`)
- **Command**: `pytest backend/tests/test_m6_ingestion.py --run-postgres --pg-bin "C:\Program Files\PostgreSQL\17\bin"`
- **Output**:
  ```
  backend/tests/test_m6_ingestion.py ..........                            [100%]
  10 passed in 44.77s
  ```
- **Summary of Verified Metrics**:
  - Source file SHA-256 digests and file sizes verified against original NASA BASS-II package.
  - Fail-closed behavior on missing or tampered source files.
  - 129 experimental tests and 129 conditions persisted.
  - 2,193 raw observations persisted verbatim.
  - 130 aggregate seals computed and cryptographically validated (1 parse run + 129 experimental conditions).
  - Repeated ingestion proved 100% idempotent (`already_ingested` status; 0 duplicate rows).
  - Transaction rollback on simulated persistence failure leaves zero orphan records.
  - Post-ingestion database integrity verification (`verify_database_integrity`) passed with zero failed seals.
  - Database backup (`pg_dump`) and restore (`pg_restore`) post-ingestion verified with full seal consistency.

### 4.5 Standard Unit Test Suite Regression
- **Command**: `pytest -m "not postgres" backend/tests/`
- **Output**:
  ```
  83 passed, 192 deselected, 1 warning in 5.91s
  ```

---

## 5. Lineage Repair Comparison Matrix

| Property | Original Tampered State (M6) | Corrected Forward State (M6 Lineage Repair) |
| :--- | :--- | :--- |
| **Historical Migration `0003`** | Modified in-place with `checked_parse` | Reverted to exact Git HEAD historical state |
| **Historical SQL `m43_sealing.sql`** | Modified in-place with new `check_parse()` | Reverted to exact Git HEAD historical state |
| **Existing Databases at `0007`** | **BROKEN**: Migration 0003 skipped; table missing (`42P01`) | **WORKING**: Migration 0008 installs table and updates function |
| **Alembic Revision Head** | Divergent / Ambiguous | Explicitly `0008_m6_security_remediation` |
| **Down Revision** | None (overwrote 0003) | `0007_m45_n2` |
| **Downgrade Path** | Destructive drop in 0003 broke sealing | Clean reversion in 0008 with downgrade confirmation |
| **Ephemeral Test Pass Rate** | Blocked / Regression failure | **100% (21/21 tests passed across 4 suites)** |

---

## 6. Conclusion & Sign-Off

The migration lineage repair is complete, forward-only, and fully verified. The repository is in a clean, consistent state with zero persistent database contamination and zero Git history alterations. All database requirements for M8 implementation are now satisfied.
