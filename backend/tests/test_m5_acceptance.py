"""M5 Database Acceptance & Reliability Test Suite.

Verifies:
1. Fresh database initialization and complete migration chain 0001 through 0007.
2. Upgrade, downgrade (confirmation-protected), and re-upgrade lifecycle.
3. Test database isolation: tests cannot connect to production or persistent dev databases.
4. Automated database health checks (CLI and API endpoint).
5. Database backup creation via pg_dump.
6. Database restore into a clean disposable database via pg_restore.
7. Cryptographic seal and digest integrity post-restore:
   - Exact aggregate seal member digests match recomputed SHA-256 digests.
   - N1 applicability snapshots remain valid.
   - N2 condition-policy matching succeeds on restored database.
"""
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from alembic import command
from alembic.util import CommandError
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import DBAPIError

from app.core.config import Settings
from app.main import create_app
from app.db.backup import (
    create_backup,
    find_postgres_bin,
    restore_backup,
    verify_database_integrity,
)
from app.db.check import check_database_health
from app.db.errors import DatabaseConfigurationError
from app.db.migrations import migration_config
from app.db.n2 import n2_matches
from test_aggregate_sealing import graph, migrate, scalar, seal
from test_n1_snapshot import clone, insert
from test_variable_immutability import approve, evidence, read_row

pytestmark = pytest.mark.postgres

ALL_REVISIONS = [
    "0001_m41_baseline",
    "0002_m42_core_schema",
    "0003_m43_sealing",
    "0004_m44_n1",
    "0005_variable_immutability",
    "0006_evidence_immutability",
    "0007_m45_n2",
]


@pytest.fixture
def m5_engine(postgres_engines):
    """Provide a dedicated disposable database for each M5 test, preserving session fixture isolation."""
    owner, _ = postgres_engines
    assert owner.url.database.startswith("flare_test_")
    name = "flare_m5_" + uuid4().hex
    with owner.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        conn.exec_driver_sql(f'CREATE DATABASE "{name}"')
    engine = create_engine(owner.url.set(database=name), isolation_level="SERIALIZABLE")
    try:
        yield engine
    finally:
        engine.dispose()
        with owner.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            conn.exec_driver_sql(f'DROP DATABASE "{name}"')


# ============================================================================
# 1. Clean Installation 0001 through 0007
# ============================================================================


def test_clean_installation_0001_through_0007(m5_engine):
    """Verify clean installation from empty database through migrations 0001 to 0007."""
    admin_engine = m5_engine
    config = migration_config()

    with admin_engine.begin() as conn:
        config.attributes["connection"] = conn
        # Start at base
        command.downgrade(config, "base")
        assert inspect(conn).get_table_names(schema="public") in ([], ["alembic_version"])

        # Progressively apply each migration revision
        for rev in ALL_REVISIONS:
            command.upgrade(config, rev)

        # Verify all schemas are present
        insp = inspect(conn)
        schemas = set(insp.get_schema_names())
        assert {"public", "flare_sealing", "flare_n1", "flare_n2"}.issubset(schemas)

        # Verify all 33 domain tables exist in public
        public_tables = set(insp.get_table_names(schema="public")) - {"alembic_version"}
        assert len(public_tables) == 33

        # Verify zero schema drift against SQLAlchemy models
        command.check(config)


# ============================================================================
# 2. Upgrade, Downgrade, and Re-upgrade Lifecycle
# ============================================================================


def test_migration_lifecycle_upgrade_downgrade_reupgrade(m5_engine):
    """Verify unconfirmed downgrade is rejected, confirmed downgrade succeeds, and re-upgrade succeeds."""
    admin_engine = m5_engine
    config = migration_config()

    with admin_engine.begin() as conn:
        config.attributes["connection"] = conn
        command.upgrade(config, "0007_m45_n2")

        # 1. Unconfirmed downgrade from 0007 to 0006 is blocked
        with pytest.raises(CommandError, match="explicit"):
            migrate(conn, "downgrade", "0006_evidence_immutability")

        # 2. Confirmed downgrade down to base succeeds
        config.attributes["allow_destructive_downgrade"] = True
        command.downgrade(config, "base")
        assert scalar(conn, "SELECT to_regnamespace('flare_n2')") is None
        assert scalar(conn, "SELECT to_regnamespace('flare_n1')") is None
        assert scalar(conn, "SELECT to_regnamespace('flare_sealing')") is None

        # 3. Re-upgrade back to head succeeds cleanly
        command.upgrade(config, "head")
        assert scalar(conn, "SELECT to_regnamespace('flare_n2')") is not None
        assert scalar(conn, "SELECT to_regnamespace('flare_n1')") is not None
        assert scalar(conn, "SELECT to_regnamespace('flare_sealing')") is not None
        command.check(config)


# ============================================================================
# 3. Test Database Isolation
# ============================================================================


def test_test_database_isolation_guards():
    """Verify tests cannot accidentally connect to production or persistent dev databases."""
    # 1. Test URL cannot fall back to development URL
    with pytest.raises(DatabaseConfigurationError, match="required"):
        Settings(
            _env_file=None,
            database_url="postgresql+psycopg://user:pw@localhost/flare_dev",
            test_database_url=None,
        ).require_database_url(test=True)

    # 2. Test URL cannot target the exact same database as development URL
    with pytest.raises(DatabaseConfigurationError, match="cannot be the same"):
        Settings(
            _env_file=None,
            database_url="postgresql+psycopg://user:pw@localhost:5432/my_custom_db",
            test_database_url="postgresql+psycopg://user:pw@localhost:5432/my_custom_db",
        ).require_database_url(test=True)

    # 3. Test URL cannot use protected database names
    for protected in ["flare_dev", "flare_prod", "production", "prod", "development", "dev", "postgres"]:
        with pytest.raises(DatabaseConfigurationError, match="protected database name"):
            Settings(
                _env_file=None,
                test_database_url=f"postgresql+psycopg://user:pw@localhost:5432/{protected}",
            ).require_database_url(test=True)

    # 4. Valid isolated test database name succeeds
    valid_test = Settings(
        _env_file=None,
        database_url="postgresql+psycopg://user:pw@localhost:5432/flare_dev",
        test_database_url="postgresql+psycopg://user:pw@localhost:5432/flare_test_abcdef123456",
    )
    url = valid_test.require_database_url(test=True)
    assert url.database == "flare_test_abcdef123456"


# ============================================================================
# 4. Automated Database Health Checks
# ============================================================================


def test_automated_database_health_checks(m5_engine):
    """Verify check_database_health evaluates connectivity, isolation, schemas, and revisions."""
    admin_engine = m5_engine
    with admin_engine.begin() as conn:
        migrate(conn, "upgrade", "0007_m45_n2")

    settings = Settings(
        _env_file=None,
        database_url=admin_engine.url.render_as_string(hide_password=False),
    )

    # 1. Healthy database check
    health = check_database_health(settings, engine=admin_engine)
    assert health["status"] == "healthy"
    assert health["connected"] is True
    assert health["is_head"] is True
    assert health["current_revision"] == "0007_m45_n2"
    assert health["required_schemas_present"] is True
    assert health["transaction_isolation"] == "serializable"
    assert health["latency_ms"] is not None and health["latency_ms"] >= 0

    # 2. Unconfigured check
    unconfigured = check_database_health(Settings(_env_file=None, database_url=None))
    assert unconfigured["status"] == "not_configured"
    assert unconfigured["connected"] is False

    # 3. Degraded check (database connected, but downgraded to older revision)
    with admin_engine.begin() as conn:
        migrate(conn, "downgrade", "0006_evidence_immutability", confirmed=True)

    degraded = check_database_health(settings, engine=admin_engine)
    assert degraded["status"] == "degraded"
    assert degraded["connected"] is True
    assert degraded["is_head"] is False

    # Re-upgrade to head
    with admin_engine.begin() as conn:
        migrate(conn, "upgrade", "0007_m45_n2")


# ============================================================================
# 5. Backup, Restore, and Cryptographic Integrity Verification
# ============================================================================


def populate_test_dataset(conn):
    """Populate a complete, sealed, valid dataset with aggregate seals and N2 matcher."""
    g, archive = graph(conn, n1=True)
    inv = g["investigation"]
    ev = g["evidence_reference"]
    now = datetime.now(timezone.utc)

    # 1. Seal parse_run
    seal(conn, g, "parse_run", archive=archive)

    # Approve variable
    var_rev = approve(conn, g, g["scientific_variable"], ev)

    # Condition segment
    seg = clone(conn, g, "condition_segment", g["condition_segment"],
                scope_status="documented", segment_key="doc_seg")

    # Annotation
    ann = clone(conn, g, "semantic_annotation", g["semantic_annotation"],
                interpretation_key=f"interp_{uuid4().hex[:6]}",
                interpreted_unit="m/s", unit_status="known",
                observed_phase="not_applicable")
    seal(conn, g, "semantic_annotation", pid=ann)

    # Protocol & requirement
    protocol = clone(conn, g, "analysis_protocol", g["analysis_protocol"],
                     protocol_code=f"prot_{uuid4().hex[:6]}")
    req = insert(conn, g, "protocol_requirement",
                 protocol_id=protocol, requirement_key="req_speed",
                 target_kind="input", variable_id=g["scientific_variable"],
                 phase="not_applicable", min_count=1, max_count=1,
                 value_policy="numeric_only", stability_policy="stable_required",
                 instrument_policy="identified_required", evidence_id=ev)
    insert(conn, g, "protocol_unit_rule",
           requirement_id=req, unit_text="m/s", unit_basis="fixture",
           method="fixture", method_version="1", evidence_id=ev)
    seal(conn, g, "analysis_protocol", pid=protocol)

    # Result
    result = clone(conn, g, "analytical_result", g["analytical_result"],
                   protocol_id=protocol)
    input_elig = insert(
        conn, g, "analytical_eligibility",
        protocol_id=protocol, revision=1, observation_id=g["observation"],
        experimental_test_id=None, segment_id=None, condition_id=None,
        condition_review_id=None, eligibility_status="needs_review",
        reason="fixture", reviewer_ref="fixture", reviewed_at=now, evidence_id=ev
    )
    clone(conn, g, "result_input", g["result_input"],
          result_id=result, segment_id=seg, annotation_id=ann,
          input_role="req_speed", eligibility_id=input_elig)

    # Condition
    cond = clone(conn, g, "experimental_condition", g["experimental_condition"],
                 segment_id=seg, segment_key="doc_seg", airflow_stability="stable")
    inst = insert(conn, g, "instrument", instrument_code=f"inst_{uuid4().hex[:6]}",
                  description="sensor", evidence_id=ev)
    comp = clone(conn, g, "condition_component", g["condition_component"],
          condition_id=cond, annotation_id=ann, variable_id=g["scientific_variable"],
          instrument_id=inst, instrument_status="identified", value_status="known")
    cond_seal = seal(conn, g, "experimental_condition", pid=cond)

    cond_rev = clone(conn, g, "review_event", g["review_event"], condition_id=cond, decision="approved")
    insert(conn, g, "approval_dependency", owner_review_id=cond_rev, entry_kind="decision",
           role="condition_content", dependency_seal_id=cond_seal)
    insert(conn, g, "approval_dependency", owner_review_id=cond_rev, entry_kind="decision",
           role="variable_definition", dependency_review_id=var_rev)
    seal(conn, g, "review_event", pid=cond_rev)

    cond_elig = insert(conn, g, "analytical_eligibility",
                       protocol_id=protocol, revision=1,
                       experimental_test_id=g["experimental_test"],
                       segment_id=seg, condition_id=cond, condition_review_id=cond_rev,
                       eligibility_status="eligible", reason="verified",
                       reviewer_ref="auditor", reviewed_at=now, evidence_id=ev)
    clone(conn, g, "result_condition", g["result_condition"],
          result_id=result, condition_id=cond, eligibility_id=cond_elig)
    seal(conn, g, "analytical_result", pid=result)

    return dict(investigation=inv, result=result, condition=cond, protocol=protocol,
                ann=ann, component=comp, cond_rev=cond_rev)


def test_backup_restore_and_integrity_verification(m5_engine, tmp_path):
    """Create pg_dump backup, restore into a fresh database, and verify all seals and digests."""
    admin_engine = m5_engine
    with admin_engine.begin() as conn:
        migrate(conn, "upgrade", "0007_m45_n2")
        meta = populate_test_dataset(conn)

    # 1. Verify source database integrity before backup
    source_audit = verify_database_integrity(admin_engine)
    assert source_audit["valid"] is True
    assert source_audit["verified_seals_count"] >= 6
    assert source_audit["failed_seals_count"] == 0

    # 2. Create custom format backup via pg_dump
    backup_file = tmp_path / "flare_backup.dump"
    created = create_backup(admin_engine.url, backup_file, format="custom")
    assert created.is_file()
    assert created.stat().st_size > 0

    # 3. Create a clean separate database for restoration
    restore_dbname = "flare_test_restore_" + uuid4().hex
    restore_url = admin_engine.url.set(database=restore_dbname)

    # Create empty database using admin connection
    with admin_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        conn.exec_driver_sql(f'CREATE DATABASE "{restore_dbname}"')

    restored_engine = create_engine(restore_url, isolation_level="SERIALIZABLE")
    try:
        # 4. Restore backup into the clean database
        restore_result = restore_backup(backup_file, restore_url, confirm=True)
        assert restore_result["success"] is True
        assert restore_result["target_database"] == restore_dbname

        # 5. Verify restored database integrity
        restored_audit = verify_database_integrity(restored_engine)
        assert restored_audit["valid"] is True
        assert restored_audit["alembic_revision"] == "0007_m45_n2"
        assert restored_audit["domain_table_count"] == 33
        assert restored_audit["verified_seals_count"] == source_audit["verified_seals_count"]
        assert restored_audit["failed_seals_count"] == 0
        assert restored_audit["triggers_active"] is True
        assert restored_audit["n1_operational"] is True
        assert restored_audit["n2_operational"] is True

        # 6. Verify N2 matching evaluates identically on the restored database
        assert n2_matches(restored_engine, meta["investigation"], meta["result"]) is True

    finally:
        restored_engine.dispose()
        with admin_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            conn.exec_driver_sql(f'DROP DATABASE "{restore_dbname}"')


def test_backup_restore_plain_sql_format(m5_engine, tmp_path):
    """Create plain SQL backup via pg_dump, restore via psql, and verify integrity."""
    admin_engine = m5_engine
    with admin_engine.begin() as conn:
        migrate(conn, "upgrade", "0007_m45_n2")
        meta = populate_test_dataset(conn)

    backup_file = tmp_path / "flare_backup.sql"
    create_backup(admin_engine.url, backup_file, format="plain")
    assert backup_file.is_file()
    assert backup_file.stat().st_size > 0

    restore_dbname = "flare_test_restore_sql_" + uuid4().hex
    restore_url = admin_engine.url.set(database=restore_dbname)

    with admin_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        conn.exec_driver_sql(f'CREATE DATABASE "{restore_dbname}"')

    restored_engine = create_engine(restore_url, isolation_level="SERIALIZABLE")
    try:
        restore_result = restore_backup(backup_file, restore_url, confirm=True)
        assert restore_result["success"] is True
        audit = verify_database_integrity(restored_engine)
        assert audit["valid"] is True
        assert audit["verified_seals_count"] >= 6
        assert n2_matches(restored_engine, meta["investigation"], meta["result"]) is True
    finally:
        restored_engine.dispose()
        with admin_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            conn.exec_driver_sql(f'DROP DATABASE "{restore_dbname}"')


# ============================================================================
# 6. Database Operations Management CLI
# ============================================================================


def test_management_cli_commands(m5_engine, monkeypatch, capsys):
    """Verify app.db.manage CLI commands: status, health, verify, and migrate downgrade protection."""
    admin_engine = m5_engine
    with admin_engine.begin() as conn:
        migrate(conn, "upgrade", "0007_m45_n2")
        populate_test_dataset(conn)

    dev_url = "postgresql+psycopg://postgres:postgres@localhost:5432/flare_dev"
    test_url = admin_engine.url.render_as_string(hide_password=False)
    monkeypatch.setenv("DATABASE_URL", dev_url)
    monkeypatch.setenv("TEST_DATABASE_URL", test_url)

    from app.db.manage import main

    # 1. status
    monkeypatch.setattr("sys.argv", ["manage.py", "status", "--test"])
    ret = main()
    assert ret == 0
    out = capsys.readouterr().out
    assert '"connected": true' in out

    # 2. health
    monkeypatch.setattr("sys.argv", ["manage.py", "health", "--test"])
    ret = main()
    assert ret == 0
    out = capsys.readouterr().out
    assert '"status": "healthy"' in out

    # 3. verify
    monkeypatch.setattr("sys.argv", ["manage.py", "verify", "--test"])
    ret = main()
    assert ret == 0
    out = capsys.readouterr().out
    assert '"valid": true' in out

    # 4. migrate downgrade blocked without confirm
    monkeypatch.setattr("sys.argv", ["manage.py", "migrate", "--test", "--revision", "base"])
    ret = main()
    assert ret == 2
    err = capsys.readouterr().err
    assert "Destructive downgrade requested without --confirm-downgrade" in err


# ============================================================================
# 7. Audit Remediation Tests: F1, F3, F4, F5
# ============================================================================


def test_restore_safety_guards(m5_engine, tmp_path):
    """F1: Verify target inspection, protected target block, and populated target confirmation."""
    admin_engine = m5_engine
    with admin_engine.begin() as conn:
        migrate(conn, "upgrade", "0007_m45_n2")
        populate_test_dataset(conn)

    backup_file = tmp_path / "safety_test.dump"
    create_backup(admin_engine.url, backup_file)

    # 1. Nonexistent target database fails inspection safely
    nonexistent_url = admin_engine.url.set(database="flare_test_nonexistent_" + uuid4().hex)
    with pytest.raises(RuntimeError, match="Cannot inspect target database"):
        restore_backup(backup_file, nonexistent_url, confirm=False)

    # 2. Protected database name requires explicit confirm
    protected_url = admin_engine.url.set(database="flare_dev")
    with pytest.raises(ValueError, match="Restoring into protected database 'flare_dev' requires explicit confirm=True"):
        restore_backup(backup_file, protected_url, confirm=False)

    # 3. Populated target database requires explicit confirm
    pop_dbname = "flare_test_pop_" + uuid4().hex
    pop_url = admin_engine.url.set(database=pop_dbname)
    with admin_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        conn.exec_driver_sql(f'CREATE DATABASE "{pop_dbname}"')

    pop_engine = create_engine(pop_url, isolation_level="SERIALIZABLE")
    try:
        # Migrate pop_engine so it has tables
        with pop_engine.begin() as conn:
            migrate(conn, "upgrade", "0007_m45_n2")

        # Without confirm -> raises ValueError
        with pytest.raises(ValueError, match="is populated with 34 existing tables; restoring requires explicit confirm=True"):
            restore_backup(backup_file, pop_url, confirm=False)

        # With confirm -> succeeds
        res = restore_backup(backup_file, pop_url, confirm=True)
        assert res["success"] is True
    finally:
        pop_engine.dispose()
        with admin_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            conn.exec_driver_sql(f'DROP DATABASE "{pop_dbname}"')

    # 4. Empty target database (not protected) succeeds without confirm
    empty_dbname = "flare_test_empty_" + uuid4().hex
    empty_url = admin_engine.url.set(database=empty_dbname)
    with admin_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        conn.exec_driver_sql(f'CREATE DATABASE "{empty_dbname}"')

    empty_engine = create_engine(empty_url, isolation_level="SERIALIZABLE")
    try:
        res = restore_backup(backup_file, empty_url, confirm=False)
        assert res["success"] is True
    finally:
        empty_engine.dispose()
        with admin_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            conn.exec_driver_sql(f'DROP DATABASE "{empty_dbname}"')


def test_aggregate_integrity_detects_tampering(m5_engine):
    """F3: Verify verify_database_integrity detects modified, missing, and extra aggregate members."""
    admin_engine = m5_engine
    with admin_engine.begin() as conn:
        migrate(conn, "upgrade", "0007_m45_n2")
        meta = populate_test_dataset(conn)

    # 1. Clean audit passes with all 6 sealed aggregates verified
    audit = verify_database_integrity(admin_engine)
    assert audit["valid"] is True
    assert audit["verified_seals_count"] >= 6
    assert audit["failed_seals_count"] == 0

    # 2. Tamper: modified member row
    with admin_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        conn.exec_driver_sql("ALTER TABLE public.condition_component DISABLE TRIGGER ALL")
        conn.exec_driver_sql(f"UPDATE public.condition_component SET slot=2 WHERE id='{meta['component']}'")
        conn.exec_driver_sql("ALTER TABLE public.condition_component ENABLE TRIGGER ALL")

    tampered_audit = verify_database_integrity(admin_engine)
    assert tampered_audit["valid"] is False
    assert tampered_audit["failed_seals_count"] >= 1
    assert any("Cryptographic seal digest mismatches" in f for f in tampered_audit["failures"])

    # Revert modification
    with admin_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        conn.exec_driver_sql("ALTER TABLE public.condition_component DISABLE TRIGGER ALL")
        conn.exec_driver_sql(f"UPDATE public.condition_component SET slot=1 WHERE id='{meta['component']}'")
        conn.exec_driver_sql("ALTER TABLE public.condition_component ENABLE TRIGGER ALL")

    restored_audit = verify_database_integrity(admin_engine)
    assert restored_audit["valid"] is True

    # 3. Tamper: extra member row
    extra_id = uuid4()
    with admin_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        conn.exec_driver_sql("ALTER TABLE public.condition_component DISABLE TRIGGER ALL")
        conn.exec_driver_sql(
            f"INSERT INTO public.condition_component (investigation_id, id, condition_id, role_id, slot, variable_id, instrument_status, instrument_id, annotation_id, value_status, evidence_id, created_at) "
            f"SELECT investigation_id, '{extra_id}', condition_id, role_id, 99, variable_id, instrument_status, instrument_id, annotation_id, value_status, evidence_id, now() "
            f"FROM public.condition_component WHERE id='{meta['component']}'"
        )
        conn.exec_driver_sql("ALTER TABLE public.condition_component ENABLE TRIGGER ALL")

    extra_audit = verify_database_integrity(admin_engine)
    assert extra_audit["valid"] is False
    assert extra_audit["failed_seals_count"] >= 1

    # Remove extra row
    with admin_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        conn.exec_driver_sql("ALTER TABLE public.condition_component DISABLE TRIGGER ALL")
        conn.exec_driver_sql(f"DELETE FROM public.condition_component WHERE id='{extra_id}'")
        conn.exec_driver_sql("ALTER TABLE public.condition_component ENABLE TRIGGER ALL")

    restored_audit2 = verify_database_integrity(admin_engine)
    assert restored_audit2["valid"] is True

    # 4. Tamper: missing member row
    with admin_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        conn.exec_driver_sql("ALTER TABLE public.condition_component DISABLE TRIGGER ALL")
        conn.exec_driver_sql(f"DELETE FROM public.condition_component WHERE id='{meta['component']}'")
        conn.exec_driver_sql("ALTER TABLE public.condition_component ENABLE TRIGGER ALL")

    missing_audit = verify_database_integrity(admin_engine)
    assert missing_audit["valid"] is False
    assert missing_audit["failed_seals_count"] >= 1


def test_trigger_integrity_detects_dropped_trigger(m5_engine):
    """F4: Verify verify_database_integrity fails if a required trigger is dropped."""
    admin_engine = m5_engine
    with admin_engine.begin() as conn:
        migrate(conn, "upgrade", "0007_m45_n2")

    initial_audit = verify_database_integrity(admin_engine)
    assert initial_audit["valid"] is True
    assert initial_audit["triggers_active"] is True

    # Drop a required immutability trigger
    with admin_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        conn.exec_driver_sql("DROP TRIGGER condition_approval_seal_guard ON public.aggregate_seal")

    dropped_audit = verify_database_integrity(admin_engine)
    assert dropped_audit["valid"] is False
    assert dropped_audit["triggers_active"] is False
    assert any("condition_approval_seal_guard" in f for f in dropped_audit["failures"])

    # Recreate trigger
    with admin_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        conn.exec_driver_sql(
            "CREATE TRIGGER condition_approval_seal_guard BEFORE INSERT ON public.aggregate_seal "
            "FOR EACH ROW EXECUTE FUNCTION flare_sealing.check_condition_review()"
        )

    fixed_audit = verify_database_integrity(admin_engine)
    assert fixed_audit["valid"] is True
    assert fixed_audit["triggers_active"] is True


def test_api_health_readiness_semantics(m5_engine):
    """F5: Verify API /health returns 200 for liveness and healthy DB, and 503 for degraded/unhealthy DB."""
    admin_engine = m5_engine
    with admin_engine.begin() as conn:
        migrate(conn, "upgrade", "0007_m45_n2")

    settings = Settings(
        _env_file=None,
        database_url=admin_engine.url.render_as_string(hide_password=False),
    )
    app = create_app(settings)
    app.state.db_engine = admin_engine

    with TestClient(app) as client:
        # 1. Liveness probe (db=False): always 200, status "ok", database omitted
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "database" not in data

        # 2. Readiness check (db=True) on healthy database: 200, status "ok", database healthy
        resp_db = client.get("/api/v1/health?db=true")
        assert resp_db.status_code == 200
        data_db = resp_db.json()
        assert data_db["status"] == "ok"
        assert data_db["database"]["status"] == "healthy"
        assert data_db["database"]["connected"] is True
        assert data_db["database"]["is_head"] is True

        # 3. Readiness check on degraded database: 503, status "degraded"
        with admin_engine.begin() as conn:
            migrate(conn, "downgrade", "0006_evidence_immutability", confirmed=True)

        resp_deg = client.get("/api/v1/health?db=true")
        assert resp_deg.status_code == 503
        data_deg = resp_deg.json()
        assert data_deg["status"] == "degraded"
        assert data_deg["database"]["is_head"] is False

        # Re-upgrade to head
        with admin_engine.begin() as conn:
            migrate(conn, "upgrade", "0007_m45_n2")

        # 4. Readiness check on unavailable database: 503, status "unhealthy"
        bad_settings = Settings(
            _env_file=None,
            database_url="postgresql+psycopg://postgres:postgres@127.0.0.1:65534/nonexistent_db",
            db_connect_timeout=1,
        )
        bad_app = create_app(bad_settings)
        with TestClient(bad_app) as bad_client:
            resp_bad = bad_client.get("/api/v1/health?db=true")
            assert resp_bad.status_code == 503
            data_bad = resp_bad.json()
            assert data_bad["status"] == "unhealthy"
            assert data_bad["database"]["connected"] is False


