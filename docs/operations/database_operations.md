# FLARE — Database Operations & Disaster Recovery Manual

## 1. Scope & Architecture Overview

FLARE (Flaming Combustion Analytical Reduction Engine) operates on **PostgreSQL 17** using a strict **SERIALIZABLE** transaction isolation level. The database schema encompasses 33 approved domain entities, immutable evidence sealing, cryptographic aggregate seals (SHA-256 member digests), N1 applicability snapshotting, and N2 deterministic condition policy matching.

This manual documents operational lifecycle procedures for:
- Local development environment establishment and database separation.
- Database initialization and migration lifecycle management (`0001` through `0007`).
- Backup creation via `pg_dump` with credential isolation.
- Disaster recovery and restoration via `pg_restore` and `psql`.
- Cryptographic aggregate seal integrity verification.
- Automated health monitoring via CLI and HTTP API.
- Test database isolation safeguards preventing accidental database corruption.

---

## 2. Environment Configuration & Database Separation

FLARE strictly separates **development**, **test**, and **production** databases.

### 2.1 Required PostgreSQL Version
- PostgreSQL 17.x (tested on PostgreSQL 17.11 x86_64).
- Extensions: `pgcrypto` (automatically provisioned in migration `0001_m41_baseline`).
- Default Port: `5432`.

### 2.2 Environment Variables
Database connections are configured using Pydantic Settings with psycopg3 driver (`postgresql+psycopg://`):

```bash
# Development Database (persistent development work)
DATABASE_URL=postgresql+psycopg://postgres:your_dev_password@localhost:5432/flare_dev

# Test Database (disposable or dedicated automated testing database)
TEST_DATABASE_URL=postgresql+psycopg://postgres:your_dev_password@localhost:5432/flare_test
```

### 2.3 Strict Test Database Isolation Guards
To prevent catastrophic accidental data loss or corruption during automated test runs:
1. `TEST_DATABASE_URL` is mandatory whenever running test suites requiring database access.
2. `TEST_DATABASE_URL` is prohibited from targeting the same database as `DATABASE_URL`.
3. `TEST_DATABASE_URL` is strictly prohibited from using protected database names:
   - `flare`
   - `flare_dev`
   - `flare_prod`
   - `production`, `prod`
   - `development`, `dev`
   - `postgres`, `template1`
4. Any attempt to run tests against a protected database name or matching development database immediately raises `DatabaseConfigurationError`.

---

## 3. Database Operations Management CLI

FLARE provides a unified database management CLI: `python -m app.db.manage`.

### Command Overview

| Command | Syntax | Description |
|---|---|---|
| `status` | `python -m app.db.manage status [--test]` | Output JSON summary of connectivity, revision, and schemas. |
| `health` | `python -m app.db.manage health [--test]` | Run automated health checks (connectivity, latency, schemas, isolation). |
| `migrate` | `python -m app.db.manage migrate [--revision REV] [--confirm-downgrade] [--test]` | Apply migrations or safely downgrade. |
| `backup` | `python -m app.db.manage backup -o <path> [--format custom\|plain] [--test]` | Dump database using `pg_dump` without logging credentials. |
| `restore` | `python -m app.db.manage restore -i <path> --confirm [--test]` | Restore backup and verify database integrity. |
| `verify` | `python -m app.db.manage verify [--test]` | Run deep cryptographic seal audit and N1/N2 integrity checks. |

---

## 4. Database Migration Lifecycle

Migrations are orchestrated using Alembic across 7 versioned steps:

```
0001_m41_baseline (pgcrypto, initial schemas)
  └── 0002_m42_core_schema (33 domain tables, audit columns)
        └── 0003_m43_sealing (flare_sealing schema, triggers, immutability)
              └── 0004_m44_n1 (flare_n1 schema, applicability snapshots)
                    └── 0005_variable_immutability (definition seals, review links)
                          └── 0006_evidence_immutability (evidence seals, lineage)
                                └── 0007_m45_n2 (flare_n2 schema, matcher, review dependencies)
```

### 4.1 Applying Migrations (Upgrade to Head)
```bash
python -m app.db.manage migrate --revision head
```
Or directly via Alembic:
```bash
alembic -c backend/alembic.ini upgrade head
```

### 4.2 Destructive Downgrade Protection
FLARE enforces destructive downgrade protection. Attempting to downgrade migrations without explicit confirmation is blocked:
```bash
# BLOCKED: Exits with code 2
python -m app.db.manage migrate --revision base

# ALLOWED: Confirmed destructive downgrade
python -m app.db.manage migrate --revision base --confirm-downgrade
```

### 4.3 Verifying Zero Schema Drift
After upgrading to head, verify that the database schema precisely matches SQLAlchemy ORM definitions:
```bash
alembic -c backend/alembic.ini check
```

---

## 5. Backup Procedures

Database backups utilize PostgreSQL native tools (`pg_dump`) orchestrated by `app.db.backup` or `app.db.manage`.

### 5.1 Credential Isolation
Passwords are never passed as command-line arguments or saved in process argument lists. They are injected exclusively via the sub-process environment `PGPASSWORD`, ensuring no secrets leak into system logs, shell history, or process tables.

### 5.2 Creating a Custom Format Backup (Recommended)
The custom format (`-Fc`) is compressed, flexible, and allows selective table or schema restoration:
```bash
python -m app.db.manage backup -o /backups/flare_20261111_0200.dump --format custom
```

### 5.3 Creating a Plain SQL Format Backup
Plain SQL (`-Fp`) generates standard human-readable SQL statements:
```bash
python -m app.db.manage backup -o /backups/flare_20261111_0200.sql --format plain
```

---

## 6. Disaster Recovery & Restoration Procedures

### 6.1 Preparation for Recovery
1. Identify the target database. Restoration into protected databases (`flare_dev`, `flare_prod`, `flare`) or any database with existing tables requires explicit `--confirm`.
2. Ensure the target database exists and is empty or freshly initialized:
   ```sql
   DROP DATABASE IF EXISTS flare_recovered;
   CREATE DATABASE flare_recovered;
   ```
3. Set the connection URL in the environment or configuration.

### 6.2 Restoring from Custom Format Archive
```bash
python -m app.db.manage restore -i /backups/flare_20261111_0200.dump --confirm
```
This executes `pg_restore --no-owner` into the confirmed target database, preserving schema integrity without destructive pre-dropping. For disaster recovery into an existing cluster, restore into a freshly created, empty database (`flare_recovered`) or provide `--confirm` after verifying target readiness.

### 6.3 Restoring from Plain SQL Archive
```bash
python -m app.db.manage restore -i /backups/flare_20261111_0200.sql --confirm
```
This executes `psql` into the confirmed target database.

---

## 7. Post-Restore Cryptographic Integrity Verification

Following any database restoration or failover, a full cryptographic integrity verification must be executed to ensure that no tampering, truncation, or corruption occurred:

```bash
python -m app.db.manage verify
```

### Verification Checks Performed:
1. **Alembic Revision:** Verifies head revision matches `0007_m45_n2`.
2. **Domain Tables:** Verifies all 33 domain entities are present in schema `public`.
3. **Database Schemas:** Verifies `public`, `flare_sealing`, `flare_n1`, and `flare_n2` exist.
4. **Trigger Verification:** Verifies immutability and sealing triggers are active on core tables (`evidence_reference`, `scientific_variable`, `review_event`, `condition_review`, `analytical_result`).
5. **Cryptographic Aggregate Seal Recomputation:**
   - Reads each record in `flare_sealing.aggregate_seal`.
   - Recomputes the member row SHA-256 digest live using PostgreSQL function `flare_sealing.snapshot(target_table, target_id)`.
   - Asserts exact equality between `member_digest` and computed digest.
   - Any digest mismatch, missing member, or modified byte causes verification failure.
6. **N1 Applicability Procedures:** Verifies operational readiness of `flare_n1.resolve_applicability()`.
7. **N2 Condition-Policy Procedures:** Verifies operational readiness of `flare_n2.validate_result()`.

Sample JSON output of a successful verification:
```json
{
  "valid": true,
  "alembic_revision": "0007_m45_n2",
  "domain_table_count": 33,
  "required_schemas_present": true,
  "triggers_active": true,
  "trigger_count": 14,
  "n1_operational": true,
  "n2_operational": true,
  "verified_seals_count": 48,
  "failed_seals_count": 0,
  "seal_failures": []
}
```

---

## 8. Automated Database Health Checks

### 8.1 HTTP Health Endpoint
The REST API provides health monitoring via `/api/v1/health`:

- **Liveness Probe (no DB overhead, returns HTTP 200 OK):**
  ```bash
  GET /api/v1/health
  ```
  Returns:
  ```json
  {
    "status": "ok",
    "application_name": "FLARE Scientific Intelligence API",
    "version": "0.1.0"
  }
  ```

- **Deep Readiness Check (audits DB connectivity, revision, and isolation):**
  - **Healthy Database (HTTP 200 OK):**
    ```bash
    GET /api/v1/health?db=true
    ```
    Returns:
    ```json
    {
      "status": "ok",
      "application_name": "FLARE Scientific Intelligence API",
      "version": "0.1.0",
      "database": {
        "status": "healthy",
        "connected": true,
        "server_version": "17.11",
        "current_revision": "0007_m45_n2",
        "is_head": true,
        "required_schemas_present": true,
        "transaction_isolation": "serializable",
        "latency_ms": 1.45,
        "pool": {
          "size": 5,
          "checkedin": 5,
          "checkedout": 0,
          "overflow": 0
        }
      }
    }
    ```
  - **Unhealthy / Degraded Database (HTTP 503 Service Unavailable):**
    ```bash
    GET /api/v1/health?db=true
    ```
    Returns:
    ```json
    {
      "status": "unhealthy",
      "application_name": "FLARE Scientific Intelligence API",
      "version": "0.1.0",
      "database": {
        "status": "unhealthy",
        "connected": false,
        "error": "Database connection failed"
      }
    }
    ```

### 8.2 Health Check Evaluation Logic
- **`healthy`**: Database reachable, connected, at Alembic head `0007_m45_n2`, all required schemas present, and `transaction_isolation == serializable`.
- **`degraded`**: Database reachable, but migration revision is not head, schemas are missing, or isolation is not serializable.
- **`unavailable`**: Connection failed or database refused connection.
- **`not_configured`**: `DATABASE_URL` not set.
