# M4.1 PostgreSQL foundation

## Initial audit (recorded before implementation)

The repository has a React/Vite frontend, a FastAPI backend, preserved raw/processed BASS-II files and architecture/source documentation. Backend code contains API/configuration/schema modules and a standalone source-preserving ingestion package; app/models is a placeholder directory. There is no existing engine, database session layer, Alembic configuration or domain ORM schema to reuse.

Python: backend/.venv uses **3.12.8**, matching pyproject.toml's >=3.12 declaration. Dependencies use pip: requirements.txt supplies direct dependencies and requirements.lock.txt freezes the verified environment. No backend formatter, linter or type-checker is configured. Existing tests are test_api.py (including configuration cases) and test_csv_parser.py; there is no separate test_config.py. Existing API routes are /, /api/v1/health and /api/v1/system/info. The health endpoint means API/process availability only.

Settings currently use Pydantic Settings with backend/.env and process overrides. No local backend/.env was found. The example contains only application/CORS configuration. Existing ingestion and its tests must remain unchanged.

PostgreSQL executable detected at C:/Program Files/PostgreSQL/17/bin/postgres.exe: **17.11**. It is not on PATH. pg_isready reported no response on localhost:5432. Service enumeration was denied by the sandbox, so no installed-service status is inferred. Docker was not found on PATH or at its standard Docker Desktop executable location; it is not required. No existing server or data directory will be started, changed or migrated.

The five approved architecture deliverables and M3.4 review define the future 33 entities/140 FKs, N1/N2, seals and publication boundaries. M4.1 implements none of those domain entities or enforcement rules. Real source ingestion remains blocked until the complete enforcement acceptance suite passes.

## Implemented scope

M4.1 adds configuration, a lazy SQLAlchemy engine, session factory/request dependency, an explicit connectivity CLI and Alembic's empty baseline. It preserves all three existing API endpoints and their OpenAPI/response conventions. No database endpoint was added: API health and database availability remain separate.

**The 33-entity schema, 140 domain FKs, N1/N2 enforcement, seals, approvals, publication procedures and permissions are not implemented. No NASA data was ingested.** SERIALIZABLE is the engine default, but isolation alone does not implement the approved scientific integrity contract.

## Dependencies and installation

Direct additions are pinned in requirements.txt:

| Dependency | Version | Purpose |
| --- | --- | --- |
| SQLAlchemy | 2.0.57 | Engine, pooling, typed session factory and empty declarative metadata |
| psycopg[binary] | 3.3.8 | PostgreSQL driver with Windows-compatible bundled libpq |
| Alembic | 1.20.1 | Explicit migrations |

requirements.lock.txt preserves all 29 previous pins and adds eight pins: the three packages above, psycopg-binary 3.3.8, greenlet 3.5.6, Mako 1.4.3, MarkupSafe 3.0.4 and tzdata 2026.6. No alternate dependency manager was introduced. `pip check` reports no broken requirements. The selected releases were installed and tested with Python 3.12.8; other declared Python versions were not tested here.

From backend in PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.lock.txt
if (-not (Test-Path -LiteralPath .env)) { Copy-Item -LiteralPath .env.example -Destination .env }
```

Do not overwrite an existing .env. On POSIX use `.venv/bin/python`. The binary driver avoids requiring a compiler/libpq installation just to import the backend. [Psycopg installation](https://www.psycopg.org/psycopg3/docs/basic/install.html).

## Environment configuration

The existing Settings system loads backend/.env and then process overrides. URLs are SecretStr values and are not included in API responses. Placeholder URLs are commented in .env.example; replace them locally and never put real credentials in versioned files or command logs.

| Setting | Default | Behavior |
| --- | --- | --- |
| DATABASE_URL | Unset | Required for database operations and Alembic; optional for existing API-only operation |
| TEST_DATABASE_URL | Unset | Separate explicit `--test` connectivity target; never falls back to DATABASE_URL |
| DB_POOL_SIZE | 5 | Positive pool size, maximum 100 |
| DB_MAX_OVERFLOW | 5 | Additional connections, 0–100 |
| DB_POOL_TIMEOUT | 5 seconds | Positive checkout timeout, maximum 60 |
| DB_POOL_RECYCLE | 1800 seconds | Positive connection recycle age |
| DB_CONNECT_TIMEOUT | 5 seconds | Driver connection timeout, 1–60 |

URL shape: `postgresql+psycopg://ROLE:ENCODED_PASSWORD@localhost:5432/DATABASE`. Percent-encode special characters in username/password, for example `%40` for `@`. Use the psycopg dialect exactly; SQLite and other schemes are rejected. Host, username and database are required and ports are range-checked. Literal whitespace and query-argument credential/endpoint overrides are rejected. Supported URL query keys are sslmode, sslrootcert and application_name; connect timeout comes from Settings. Password omission is permitted for externally configured PostgreSQL authentication; no password is supplied by the application.

URL validation occurs through `Settings.require_database_url()` at engine/migration/connectivity use, rather than preventing API-only startup when the URL is unset. A supplied malformed URL fails engine/startup setup with a safe configuration error. Missing configuration never creates a database or falls back to SQLite. SecretStr masks normal representation; do not serialize raw validation inputs, enable SQL/driver debug logging or print unredacted URL objects. Database errors on the request dependency become a generic 503; the CLI prints only safe statuses.

## SQLAlchemy structure and transaction lifetime

- app/db/base.py provides an empty DeclarativeBase and deterministic constraint naming. There are no models or metadata tables.
- app/db/engine.py constructs an engine explicitly, with pre-ping, configurable pool/connect limits, SERIALIZABLE, echo disabled and parameter hiding. Engine construction does not connect.
- app/db/session.py provides a typed sessionmaker, session_scope and get_session request dependency. Every scope gets its own Session. Exceptions roll back; unfinished successful work also rolls back at cleanup. Close always releases the session. Commits must be explicit inside the operation before returning success, never hidden in dependency teardown. No global Session exists.
- app/main.py initializes one optional engine/factory per application lifespan and disposes it at shutdown. It never calls create_all or runs migrations. Existing API routes do not acquire database sessions.
- app/db/check.py runs SELECT 1 through SQLAlchemy, returning only available/unavailable/not_configured/invalid_configuration. app/db/errors.py defines safe configuration errors.
- app/db/migrations.py supplies an absolute Alembic config path and supports explicit Settings/connection injection for testing.

No automatic transaction retry is introduced: later controlled scientific operations must retry the entire appropriate transaction under the approved rules. Session pooling must not be mistaken for a cached analytical permission. [SQLAlchemy session lifecycle](https://docs.sqlalchemy.org/en/20/orm/session_basics.html).

## Local PostgreSQL and role setup

Docker is optional and no Docker configuration was added. Use an existing local installation or install PostgreSQL separately. The verified binary directory here is C:/Program Files/PostgreSQL/17/bin. Do not point initdb at an existing data directory.

For a developer-managed server, an administrator can explicitly provision separate migration and application roles. The following is a **manual setup example**, not SQL executed by this implementation. Run in psql as an authorized local administrator; `\password` prompts rather than placing a password in SQL history:

```sql
CREATE ROLE flare_migrator LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE;
\password flare_migrator
CREATE ROLE flare_app LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE;
\password flare_app
CREATE DATABASE flare_dev OWNER flare_migrator;
\connect flare_dev
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT CONNECT ON DATABASE flare_dev TO flare_app;
GRANT USAGE ON SCHEMA public TO flare_app;
```

Do not rerun creation commands blindly if names already exist. The application role is not schema/database owner and has no scientific-table privileges. Later publication/security-definer permission design remains deferred.

For a manually managed disposable database, choose a fresh `flare_test_<32-hex-UUID>` name and explicitly create it under the migration role, never repurpose flare_dev. Supply TEST_DATABASE_URL only to the safe read-only `--test` checker. The automated migration suite does **not** accept this URL: it creates its own private cluster/database, preventing accidental downgrade of a development or production database.

## Alembic setup and commands

backend/alembic.ini contains paths only, not a connection string. migrations/env.py reads application Settings, passes the URL directly to SQLAlchemy/Alembic without config-file percent interpolation, and supports PostgreSQL only. Metadata integration is prepared for future explicitly imported models. The template has typed revision identifiers; the fixed initial revision is `0001_m41_baseline` with no parent. Its upgrade/downgrade functions do nothing. Only Alembic's bookkeeping table can be created.

From backend:

```powershell
.\.venv\Scripts\python.exe -m alembic heads
# Set DATABASE_URL locally to the migration role for the intended database first.
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m alembic current
```

Restore the runtime application-role URL before starting the API. Migrations are never run by application startup. Do not put migration credentials in alembic.ini or grant the runtime role ownership. On a known disposable database only, downgrade with `python -m alembic downgrade base`; it removes the baseline version row, and Alembic's empty bookkeeping table may remain. Future domain migration changes require the later milestone.

## API and database checks

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
# In another terminal, from backend:
.\.venv\Scripts\python.exe -m app.db.check
.\.venv\Scripts\python.exe -m app.db.check --test
```

The CLI exits 0 only for available; all other statuses exit 1. A running API with no DATABASE_URL still returns the original healthy API response. This does not imply database or dataset availability. Current developer DB status is **not_configured**: no local .env or persistent development database was provisioned. Integration connectivity below was to a disposable cluster only. The initial localhost:5432 no-response result was obtained inside the sandbox; later process inspection showed other PostgreSQL processes, which were neither accessed nor changed. Do not infer that the user's installed server is stopped from the sandbox probe.

## Tests and verification results

Use backend as the working directory and an explicit pytest config:

```powershell
# Existing regression suite: 40 tests
.\.venv\Scripts\python.exe -m pytest -c pyproject.toml tests/test_api.py tests/test_csv_parser.py -q

# New configuration/infrastructure/Alembic unit tests: 31 tests; no database required
.\.venv\Scripts\python.exe -m pytest -c pyproject.toml tests/test_db_config.py tests/test_db_infrastructure.py tests/test_migrations.py -q

# All tests; PostgreSQL tests skip explicitly unless opted in
.\.venv\Scripts\python.exe -m pytest -c pyproject.toml tests -q

# All tests plus private-cluster PostgreSQL integration
.\.venv\Scripts\python.exe -m pytest -c pyproject.toml tests -q --run-postgres '--pg-bin=C:/Program Files/PostgreSQL/17/bin'
```

On POSIX, pass the directory containing initdb/pg_ctl and run as a non-root user. Alternatively set POSTGRES_BIN or place initdb on PATH. With --run-postgres, unavailable binaries or startup failure fail the tests rather than count as a pass. Without that option, the three integration tests skip explicitly.

The session fixture initializes a private temporary cluster with UTF-8 and SCRAM, a random loopback port/database/password and a separate non-superuser, non-owner application role. It never connects to DATABASE_URL or TEST_DATABASE_URL and never migrates an existing database. The plaintext initialization password file is removed immediately after initdb. SQL identifiers/DDL literals use psycopg's quoting objects; connection values are passed as parameters. The cluster stops in finally; diagnostic files remain under pytest's temporary directory retention policy. PostgreSQL output goes to a file to avoid inherited-pipe hangs on Windows. The fixture's administrator exists only inside this disposable cluster, not in any developer/application database.

Final verification on Python 3.12.8 / PostgreSQL **17.11**:

| Check | Result |
| --- | --- |
| Existing API/parser regressions | 40 passed; original tests unchanged |
| New configuration tests | 18 passed |
| New infrastructure/request-session tests | 10 passed |
| New Alembic unit tests | 3 passed, including offline SQL with only the version table |
| Actual PostgreSQL integration | 3 passed: SELECT 1, SERIALIZABLE/non-owner application role, recovery after a failed SQL transaction, upgrade/check/downgrade on a fresh private database |
| Combined final suite | **74 passed, 1 warning in 17.84 seconds** |
| Migration effects | Only alembic_version after upgrade; no domain tables; clean autogenerate check; no current revision after downgrade |
| FastAPI compatibility | Lifespan startup/shutdown, root/health/system responses, CORS and exact OpenAPI route set pass |
| Dependencies | pip check passes; all 29 prior lock pins preserved |
| Static tooling | No backend formatter/linter/type checker configured; none claimed to run |

The warning is the pre-existing StarletteDeprecationWarning about httpx TestClient and a suggested httpx2 migration. No unrelated dependency migration was made.

Earlier attempts are not hidden: a root-directory pytest command initially failed to locate app; the documented backend/config invocation fixes discovery. A custom-option invocation without explicit config misidentified the PostgreSQL binary directory as pytest root and ran no tests. Sandbox pip DNS failed and sandbox pytest stalled; installation and the actual test runs used approved execution outside the sandbox. The first private-cluster run had 69 passes/3 setup errors because Windows inherited captured subprocess pipes; the owned cluster was stopped, the fixture was corrected to file output, and the complete suite then passed. No existing server was stopped.

## Exact files changed

Modified:

- backend/requirements.txt
- backend/requirements.lock.txt
- backend/pyproject.toml
- backend/.env.example
- backend/app/core/config.py
- backend/app/main.py

Created:

- backend/alembic.ini
- backend/app/db/__init__.py
- backend/app/db/base.py
- backend/app/db/check.py
- backend/app/db/engine.py
- backend/app/db/errors.py
- backend/app/db/migrations.py
- backend/app/db/session.py
- backend/migrations/env.py
- backend/migrations/script.py.mako
- backend/migrations/versions/0001_m41_baseline.py
- backend/tests/conftest.py
- backend/tests/test_db_config.py
- backend/tests/test_db_infrastructure.py
- backend/tests/test_migrations.py
- backend/tests/test_postgres_integration.py
- docs/implementation/m4_1_postgresql_foundation.md

## Preservation and limits

Baseline hash comparison confirms all 80 other checked existing files are unchanged, including approved architecture/reviews, raw/processed NASA files, ingestion modules/tests and frontend files. Only config.py and main.py changed within the previously hashed application/test/document trees; new infrastructure/tests/documentation and the six listed configuration/dependency edits are intentional.

No NASA data was ingested, no scientific values were normalized, and no annotations/approvals were created. No domain schema, publication enforcement, analytics or AI/RAG is implemented. No Git commit, amend or push occurred. A persistent developer database and real credentials still require local operator configuration. M4.1 is complete at the infrastructure/test level; do not proceed automatically to M4.2 or real ingestion.
