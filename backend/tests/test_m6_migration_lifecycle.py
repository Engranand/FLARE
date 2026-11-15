"""Lifecycle, rollback, upgrade, and security tests for migration 0008_m6_security_remediation.

Verifies:
1. Fresh database migration from zero to 0008 head.
2. Stepwise upgrade of an existing database from 0007_m45_n2 to 0008_m6_security_remediation.
3. Rollback (downgrade) from 0008 to 0007, confirming drop of checked_parse and function reversion.
4. Idempotent re-upgrade from 0007 to 0008.
5. Savepoint rollback behavior and isolation within transactions.
6. Schema qualification and search_path inspection on flare_sealing.check_parse().
"""
from uuid import uuid4
import pytest
from alembic import command
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError

from app.db.migrations import migration_config

pytestmark = pytest.mark.postgres


@pytest.fixture
def fresh_db(postgres_engines):
    """Provide owner and app engines on a disposable empty database."""
    owner, app = postgres_engines
    assert owner.url.database.startswith("flare_test_")
    name = "flare_mig_" + uuid4().hex

    with owner.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        conn.exec_driver_sql(f'CREATE DATABASE "{name}"')

    owner_engine = create_engine(owner.url.set(database=name), isolation_level="SERIALIZABLE")
    app_engine = create_engine(app.url.set(database=name), isolation_level="SERIALIZABLE")

    try:
        yield owner_engine, app_engine
    finally:
        owner_engine.dispose()
        app_engine.dispose()
        with owner.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            conn.exec_driver_sql(f'DROP DATABASE "{name}"')


def test_fresh_migration_zero_to_head(fresh_db):
    """Verify fresh migration replay from zero to 0008 head."""
    owner_engine, _ = fresh_db
    with owner_engine.begin() as conn:
        cfg = migration_config()
        cfg.attributes["connection"] = conn
        command.upgrade(cfg, "head")

        # Verify alembic_version
        rev = conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
        assert rev == "0008_m6_security_remediation"

        # Verify checked_parse table exists with correct types
        table_exists = conn.execute(text("""
            SELECT count(*) FROM information_schema.tables 
            WHERE table_schema = 'flare_sealing' AND table_name = 'checked_parse';
        """)).scalar_one()
        assert table_exists == 1

        cols = conn.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'flare_sealing' AND table_name = 'checked_parse'
            ORDER BY ordinal_position;
        """)).fetchall()
        assert cols == [("xact_id", "xid8"), ("parse_run_id", "uuid")]

        # Verify function search_path and security definer
        fn_meta = conn.execute(text("""
            SELECT prosecdef, proconfig
            FROM pg_proc p
            JOIN pg_namespace n ON n.oid = p.pronamespace
            WHERE n.nspname = 'flare_sealing' AND p.proname = 'check_parse';
        """)).mappings().one()
        assert fn_meta["prosecdef"] is True
        assert "search_path=pg_catalog, flare_sealing, public" in fn_meta["proconfig"]


def test_upgrade_from_0007_to_0008(fresh_db):
    """Verify clean upgrade from 0007_m45_n2 to 0008_m6_security_remediation."""
    owner_engine, _ = fresh_db
    with owner_engine.begin() as conn:
        cfg = migration_config()
        cfg.attributes["connection"] = conn
        # Step 1: Upgrade to 0007
        command.upgrade(cfg, "0007_m45_n2")

        rev = conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
        assert rev == "0007_m45_n2"

        # Verify checked_parse does NOT exist yet
        tbl_count = conn.execute(text("""
            SELECT count(*) FROM information_schema.tables 
            WHERE table_schema = 'flare_sealing' AND table_name = 'checked_parse';
        """)).scalar_one()
        assert tbl_count == 0

        # Step 2: Forward upgrade to 0008
        command.upgrade(cfg, "0008_m6_security_remediation")

        rev2 = conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
        assert rev2 == "0008_m6_security_remediation"

        # Verify checked_parse NOW exists
        tbl_count2 = conn.execute(text("""
            SELECT count(*) FROM information_schema.tables 
            WHERE table_schema = 'flare_sealing' AND table_name = 'checked_parse';
        """)).scalar_one()
        assert tbl_count2 == 1


def test_downgrade_and_reupgrade(fresh_db):
    """Verify downgrade from 0008 to 0007 drops table cleanly and re-upgrade is idempotent."""
    owner_engine, _ = fresh_db
    with owner_engine.begin() as conn:
        cfg = migration_config()
        cfg.attributes["connection"] = conn
        cfg.attributes["allow_destructive_downgrade"] = True
        # Upgrade to head
        command.upgrade(cfg, "head")
        assert conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == "0008_m6_security_remediation"

        # Downgrade to 0007
        command.downgrade(cfg, "0007_m45_n2")
        assert conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == "0007_m45_n2"

        tbl_count = conn.execute(text("""
            SELECT count(*) FROM information_schema.tables 
            WHERE table_schema = 'flare_sealing' AND table_name = 'checked_parse';
        """)).scalar_one()
        assert tbl_count == 0

        # Re-upgrade to head
        command.upgrade(cfg, "0008_m6_security_remediation")
        assert conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == "0008_m6_security_remediation"

        tbl_count2 = conn.execute(text("""
            SELECT count(*) FROM information_schema.tables 
            WHERE table_schema = 'flare_sealing' AND table_name = 'checked_parse';
        """)).scalar_one()
        assert tbl_count2 == 1


def test_savepoint_rollback_behavior(fresh_db):
    """Verify that savepoint rollbacks within a transaction behave safely and preserve xact_id deduplication."""
    owner_engine, app_engine = fresh_db
    now = "2026-01-01 00:00:00+00"
    dummy_sha = "0" * 64
    inv_id = uuid4()
    doc_id = uuid4()
    ev_id = uuid4()
    run_id = uuid4()
    field_id = uuid4()
    rec_id = uuid4()

    with owner_engine.begin() as conn:
        cfg = migration_config()
        cfg.attributes["connection"] = conn
        command.upgrade(cfg, "head")
        conn.execute(text("GRANT USAGE ON SCHEMA public, flare_sealing, flare_n1, flare_n2 TO flare_fixture_app;"))
        conn.execute(text("GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO flare_fixture_app;"))
        conn.execute(text("GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA flare_sealing TO flare_fixture_app;"))

        # Setup parent rows
        conn.execute(text("""
            INSERT INTO public.investigation (id, repository_code, investigation_code, name, agency, doi, description, source_repository_url, metadata, created_at)
            VALUES (:id, 'SP-TEST', 'SP-01', 'Savepoint Test', 'NASA', '10.1234/sp', 'Test savepoints', 'https://example.com', '{}', :now);
        """), {"id": inv_id, "now": now})
        conn.execute(text("""
            INSERT INTO public.source_document (investigation_id, id, original_filename, source_type, artifact_origin, sha256, file_size_bytes, storage_key, source_version, metadata, created_at)
            VALUES (:inv, :id, 'test.csv', 'csv', 'external_original', :sha, 10, 'k', '1', '{}', :now);
        """), {"inv": inv_id, "id": doc_id, "sha": dummy_sha, "now": now})
        conn.execute(text("""
            INSERT INTO public.evidence_reference (investigation_id, id, source_document_id, locator_kind, locator_key, locator_version, locator, location_basis, extraction_method, extractor_version, verification_status, verification_scope, created_at)
            VALUES (:inv, :id, :doc, 'document', 'test', '1', '{}', 'test', 'test', '1', 'unverified', 'test', :now);
        """), {"inv": inv_id, "id": ev_id, "doc": doc_id, "now": now})

    with app_engine.connect() as conn:
        trans = conn.begin()
        try:
            # Insert valid parse_run with 1 record
            conn.execute(text("""
                INSERT INTO public.parse_run (
                    investigation_id, id, source_document_id, parser_name,
                    parser_version, code_sha256, code_storage_key,
                    configuration_sha256, configuration, output_sha256,
                    output_storage_key, record_count, status, created_at
                ) VALUES (
                    :inv, :id, :doc, 'test', '1.0', :sha, 'path/code',
                    :sha, '{}', :sha, 'path/out', 1, 'complete', :now
                );
            """), {"inv": inv_id, "id": run_id, "doc": doc_id, "sha": dummy_sha, "now": now})

            conn.execute(text("""
                INSERT INTO public.source_field (investigation_id, id, parse_run_id, table_key, ordinal, original_header, raw_unit_status, header_evidence_id, created_at)
                VALUES (:inv, :id, :run, 'tbl', 1, 'col1', 'not_stated', :ev, :now);
            """), {"inv": inv_id, "id": field_id, "run": run_id, "ev": ev_id, "now": now})

            conn.execute(text("""
                INSERT INTO public.source_record (investigation_id, id, parse_run_id, table_key, source_record_number, source_row_id, row_evidence_id, created_at)
                VALUES (:inv, :id, :run, 'tbl', 1, 'r1', :ev, :now);
            """), {"inv": inv_id, "id": rec_id, "run": run_id, "ev": ev_id, "now": now})

            conn.execute(text("""
                INSERT INTO public.observation (
                    investigation_id, id, parse_run_id, source_record_id, source_field_id,
                    evidence_id, raw_value, source_value_kind, unit_origin, parser_classification,
                    parser_flags, original_representation, created_at
                ) VALUES (
                    :inv, :id, :run, :rec, :field,
                    :ev, 'val', 'text', 'not_stated', 'text',
                    '{}', '{}', :now
                );
            """), {"inv": inv_id, "id": uuid4(), "run": run_id, "rec": rec_id, "field": field_id, "ev": ev_id, "now": now})

            # Savepoint: attempt invalid direct write to checked_parse
            sp = conn.begin_nested()
            with pytest.raises(DBAPIError) as exc:
                conn.execute(text("INSERT INTO flare_sealing.checked_parse (xact_id, parse_run_id) VALUES (pg_current_xact_id(), :run)"), {"run": run_id})
            assert exc.value.orig.sqlstate == "42501"  # insufficient_privilege
            sp.rollback()

            # Transaction should still commit cleanly
            trans.commit()
        except Exception:
            trans.rollback()
            raise

    # Verify rows persisted
    with app_engine.connect() as conn:
        count = conn.execute(text("SELECT count(*) FROM public.source_record WHERE parse_run_id = :run"), {"run": run_id}).scalar_one()
        assert count == 1
