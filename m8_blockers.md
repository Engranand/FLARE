# FLARE — Milestone 8 Pre-Implementation Blockers Report

**Milestone**: M8 — Ingestion Engine Implementation Readiness  
**Author**: FLARE Scientific Data Engineer & Systems Pre-Implementation Auditor  
**Date**: 2026-11-14  
**Audit Status**: READ-ONLY Pre-Implementation Assessment  
**Overall Verdict**: **NOT READY FOR M8 IMPLEMENTATION**  

---

## 1. Executive Summary

A rigorous, read-only pre-implementation review of the FLARE repository was conducted prior to initiating Milestone 8 (Ingestion Engine Implementation). While the domain data architecture (33 approved tables in `0002_m42_core_schema.py`) is fully capable of supporting the BASS-II data model, **five critical blockers** in the database migration lineage, repository working tree state, and security remediation architecture prevent safe, production-grade M8 implementation.

Milestone 8 implementation must not proceed until all five blockers detailed below are resolved.

---

## 2. Detailed Technical Blockers

### Blocker 1: Historical Migration Tampering & Alembic Lineage Corruption
- **Severity**: **CRITICAL (Showstopper)**
- **Affected Files**:
  - `backend/migrations/versions/0003_m43_sealing.py` (lines 49, 94)
  - `backend/migrations/versions/m43_sealing.sql` (lines 141–165)
- **Technical Description**:
  During Milestone 6 database-security remediation, the PostgreSQL trigger deduplication mechanism was refactored to eliminate client-settable GUC parameters (`flare.parse_run_checked`). However, this remediation was implemented by **modifying historical migration `0003_m43_sealing.py` and `m43_sealing.sql` directly in place**, adding:
  ```sql
  CREATE UNLOGGED TABLE flare_sealing.checked_parse (
      xact_id xid8,
      parse_run_id uuid,
      PRIMARY KEY (xact_id, parse_run_id)
  );
  ```
  and altering `flare_sealing.check_parse()` to `SECURITY DEFINER`.
- **System Impact**:
  In Alembic, applied revisions are tracked in `public.alembic_version`. Any persistent database instance (development, staging, CI, or production) that has already executed revision `0003` will never re-execute it. Running `alembic upgrade head` does nothing. Consequently:
  1. `flare_sealing.checked_parse` will **NOT exist** on existing databases.
  2. The function `flare_sealing.check_parse()` will remain in its obsolete, vulnerable GUC-dependent state.
  3. When M8 ingestion inserts rows into `observation` or `source_record`, the deferred trigger `check_parse()` will fail with:
     ```
     ERROR: relation "flare_sealing.checked_parse" does not exist (SQLSTATE 42P01)
     ```
  4. This violates the core architectural requirement of **migration immutability** and breaks database upgrade reproducibility.
- **Required Remediation**:
  1. Revert `backend/migrations/versions/0003_m43_sealing.py` and `m43_sealing.sql` to their pristine historical states.
  2. Create a clean forward migration: `backend/migrations/versions/0008_m6_security_remediation.py` (down_revision: `0007_m45_n2`).
  3. In `0008`, issue `CREATE UNLOGGED TABLE IF NOT EXISTS flare_sealing.checked_parse (...)` and `CREATE OR REPLACE FUNCTION flare_sealing.check_parse() ...`.

---

### Blocker 2: Uncommitted Working Tree State & Unversioned Pipeline Infrastructure
- **Severity**: **HIGH (Process & Reproducibility Blocker)**
- **Affected Files**:
  - 10 modified tracked files: `backend/migrations/versions/0003_m43_sealing.py`, `m43_sealing.sql`, `backend/app/api/routes.py`, `backend/app/core/config.py`, `backend/app/db/check.py`, `backend/app/schemas/system.py`, `backend/tests/test_api.py`, `backend/tests/test_migrations.py`, `backend/tests/test_n1_snapshot.py`, `backend/tests/test_reviewed_evidence.py`.
  - 18 untracked files: `backend/app/ingestion/pipeline.py`, `backend/app/ingestion/reconciliation.py`, `backend/app/db/backup.py`, `backend/app/db/manage.py`, `backend/app/db/n2.py`, `backend/app/services/identity.py`, `backend/migrations/versions/0007_m45_n2.py`, `backend/migrations/versions/m45_n2.sql`, `backend/tests/test_m6_guc_remediation.py`, `backend/tests/test_m6_ingestion.py`, etc.
- **Technical Description**:
  The Git repository currently contains only one initial commit (`78cd194`). All foundational work developed across Milestones 4, 5, and 6 sits uncommitted in the local working directory.
- **System Impact**:
  Attempting to execute Milestone 8 on an uncommitted codebase makes it impossible to isolate regressions, establish reproducible CI/CD test runs, or perform safe Git rollbacks if an ingestion error occurs.
- **Required Remediation**:
  Complete a milestone sealing pass: run all pytest suites cleanly against a disposable test database, stage verified M4/M5/M6 files, and commit them cleanly before starting M8 implementation turns.

---

### Blocker 3: SECURITY DEFINER Trigger Surface Area & UNLOGGED Table Operational Risks
- **Severity**: **MEDIUM (Security & Operational Robustness)**
- **Affected File**: `backend/migrations/versions/m43_sealing.sql` (lines 141–165)
- **Technical Description**:
  The remediated trigger function `flare_sealing.check_parse()` is declared with `SECURITY DEFINER SET search_path = pg_catalog, flare_sealing, public`.
  1. `flare_sealing.check_parse()` executes upon every child insert (invoked deferred for all 2,193 observations in BASS-II). Because it runs with superuser/owner rights, any logic error or unhandled exception during parse shape validation executes in a privileged context.
  2. `flare_sealing.checked_parse` is declared `UNLOGGED`. In PostgreSQL, unlogged tables bypass the Write-Ahead Log (WAL) to minimize I/O overhead. However, PostgreSQL truncates unlogged tables immediately upon an unexpected server crash or restart, and unlogged tables are empty on streaming replication standbys.
- **System Impact**:
  If a PostgreSQL failover or restart occurs during an in-flight SERIALIZABLE transaction batch, the `checked_parse` table will be empty, while the transaction state may attempt to re-read or conflict on `pg_current_xact_id()`.
- **Required Remediation**:
  1. Verify and document that `flare_sealing.checked_parse` is accessed strictly within active serializable transaction boundaries.
  2. Add an explicit database privilege grant in the forward migration: ensure the application role (`flare_app`) has `USAGE` on schema `flare_sealing` and `EXECUTE` on the function, but is strictly denied `INSERT/UPDATE/DELETE` on `checked_parse` directly.

---

### Blocker 4: Typographical Hash Discrepancies in M7 Audit Report Section 7.1
- **Severity**: **LOW (Documentation & Compliance Defect)**
- **Affected File**: `m7_scientific_audit_report.md` (Section 7.1 table)
- **Technical Description**:
  Section 7.1 of `m7_scientific_audit_report.md` lists placeholder SHA-256 strings for several priority datasets instead of the true cryptographic digests computed from disk:
  - `PSI-25_Experimental table_BASS-II.csv`: Listed as `8390bbf4ad8cb0cf03e838ff40c9ae77a76c8c4a4e17ca8eef2fcfb61ff62c3f`, whereas true disk hash is `71e792bf6b5fb5ea620c5dd70fbbac05515992e12aefcf5dff47312caa48c042`.
  - `PSI-100_Raw Data_Raw telemetry file.csv`: Listed as `5e9ce6d220b3...`, whereas true disk hash is `dfb204ce3bdf8b1749652549afcbad31d180902bc268dfbe782c70fa38d170a2`.
  - `PSI-20_Experimental table_ACME BRE.csv`: Listed as `df943d04...`, whereas true disk hash is `4aa5d3f98708ceacced5c620d46858b9965f8d4d941b203229f46467d53e5ab7`.
  - `PSI-159_Experimental table_CFI-G_Normal Flames.csv`: Listed as `2e08aeeb...`, whereas true disk hash is `d95a621c3fbd27d204dd32ed29fa17d68f2b779d6a523cde8479ed7ebaa5251a`.
  - `PSI-102_Experimental table_SAME.csv`: Listed as `6908db63...`, whereas true disk hash is `268d1e121d2f211b124407dd32b9475617bd269ede2c2d1749441da3e949a2af`.
- **System Impact**:
  While `scientific_dataset_inventory.csv` and `scientific_dataset_profile.json` contain the exact, true disk hashes, automated compliance checkers reading the Markdown summary report will flag cryptographic verification failures.
- **Required Remediation**:
  Update Section 7.1 of `m7_scientific_audit_report.md` with the verified disk hashes.

---

### Blocker 5: Hardcoded Source Path Coupling in Ingestion Reconciliation
- **Severity**: **LOW (Configuration & Flexibility Defect)**
- **Affected File**: `backend/app/ingestion/reconciliation.py` (lines 28–42)
- **Technical Description**:
  The existing pipeline code in `backend/app/ingestion/reconciliation.py` defines source paths hardcoded to `data/raw/bass_ii/original/`:
  ```python
  SOURCE_FILES = {
      "csv": {"relative_path": "data/raw/bass_ii/original/PSI-25_Experimental table_BASS-II.csv"},
      "xlsx": {"relative_path": "data/raw/bass_ii/original/BASS-II Test Matrix by PI Final.xlsx"},
      "docx": {"relative_path": "data/raw/bass_ii/original/BASS-II data FAQ.docx"},
  }
  ```
  However, the challenge acquisition repository acquired the complete official NASA challenge structure under `data/raw/challenge_resources/original/bass_ii/`.
- **System Impact**:
  If the ingestion engine is invoked in an environment where only `challenge_resources/` is mounted, `verify_source_integrity()` will fail closed with `SourceError: Source file missing`.
- **Required Remediation**:
  Allow path resolution in `reconciliation.py` to accept an explicit dataset directory root or check both canonical locations with identical SHA-256 validation.

---

## 3. Remediation Roadmap to Achieve "READY FOR M8"

```
                              M8 READINESS REMEDIATION WORKFLOW
  ┌────────────────────────────────────────────────────────────────────────────────────────┐
  │ 1. REVERT HISTORICAL TAMPERING:                                                        │
  │    git checkout backend/migrations/versions/0003_m43_sealing.py                        │
  │    git checkout backend/migrations/versions/m43_sealing.sql                            │
  ├────────────────────────────────────────────────────────────────────────────────────────┤
  │ 2. CREATE CLEAN FORWARD MIGRATION:                                                     │
  │    Create backend/migrations/versions/0008_m6_security_remediation.py                  │
  │    - Creates flare_sealing.checked_parse                                               │
  │    - Installs hardened flare_sealing.check_parse() with SECURITY DEFINER               │
  ├────────────────────────────────────────────────────────────────────────────────────────┤
  │ 3. CORRECT DOCUMENTATION DEFECT:                                                       │
  │    Update m7_scientific_audit_report.md Section 7.1 table with true SHA-256 digests    │
  ├────────────────────────────────────────────────────────────────────────────────────────┤
  │ 4. EXECUTE FULL TEST SUITE:                                                            │
  │    pytest backend/tests/test_m6_guc_remediation.py backend/tests/test_m6_ingestion.py   │
  ├────────────────────────────────────────────────────────────────────────────────────────┤
  │ 5. STAGE & COMMIT PREREQUISITES:                                                       │
  │    git add backend/ docs/ && git commit -m "feat(m6): complete database security..."   │
  ├────────────────────────────────────────────────────────────────────────────────────────┤
  │ 6. FORMAL VERDICT TRANSITION:                                                          │
  │    Transition verdict from NOT READY to READY FOR M8 IMPLEMENTATION                    │
  └────────────────────────────────────────────────────────────────────────────────────────┘
```
