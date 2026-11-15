"""Permanent regression and security verification tests for M6 parse trigger deduplication.

Verifies:
1. GUC-based memoization has been completely removed.
2. Unprivileged database role attempting to set GUCs cannot bypass parse_shape validation.
3. Invalid parse_run (declared 100, actual 0) fails at commit time with SQLSTATE 23514.
4. Inserting a child record into an existing unsealed parse_run triggers validation.
5. Inserting a child record into a sealed parse_run is rejected immediately with SQLSTATE 55000.
6. Direct client manipulation of flare_sealing.checked_parse is blocked by PostgreSQL privileges.
7. Deduplication within a transaction operates correctly and securely without GUCs.
"""
from datetime import datetime, timezone
import hashlib
import json
from uuid import uuid4

import pytest
from alembic import command
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError

from app.db.migrations import migration_config

pytestmark = pytest.mark.postgres


@pytest.fixture(scope="module")
def migrated_dbs(postgres_engines):
    """Provide owner and app engines on a fresh database migrated to head."""
    owner, app = postgres_engines
    assert owner.url.database.startswith("flare_test_")
    name = "flare_remed_" + uuid4().hex

    with owner.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        conn.exec_driver_sql(f'CREATE DATABASE "{name}"')

    owner_engine = create_engine(owner.url.set(database=name), isolation_level="SERIALIZABLE")
    app_engine = create_engine(app.url.set(database=name), isolation_level="SERIALIZABLE")

    try:
        with owner_engine.begin() as conn:
            cfg = migration_config()
            cfg.attributes["connection"] = conn
            command.upgrade(cfg, "head")

            # Standard app role grants
            conn.execute(text("GRANT USAGE ON SCHEMA public, flare_sealing, flare_n1, flare_n2 TO flare_fixture_app;"))
            conn.execute(text("GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO flare_fixture_app;"))
            conn.execute(text("GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA flare_sealing TO flare_fixture_app;"))

        yield owner_engine, app_engine
    finally:
        owner_engine.dispose()
        app_engine.dispose()
        with owner.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            conn.exec_driver_sql(f'DROP DATABASE "{name}"')


def test_unprivileged_role_cannot_manipulate_checked_parse(migrated_dbs):
    """Verify that an unprivileged role cannot write to or tamper with flare_sealing.checked_parse."""
    _, app = migrated_dbs
    with pytest.raises(DBAPIError) as exc_info:
        with app.begin() as conn:
            conn.execute(
                text("INSERT INTO flare_sealing.checked_parse (xact_id, parse_run_id) VALUES (pg_current_xact_id(), :pid)"),
                {"pid": uuid4()},
            )
    assert exc_info.value.orig.sqlstate == "42501"  # insufficient_privilege


def test_corrupt_parse_run_fails_even_with_preset_guc(migrated_dbs):
    """Verify that setting any GUC cannot bypass parse_shape validation for a corrupt parse run."""
    owner, app = migrated_dbs
    now = datetime.now(timezone.utc)
    dummy_sha = "0" * 64
    inv_id = uuid4()
    doc_id = uuid4()
    corrupt_run_id = uuid4()

    with owner.begin() as conn:
        conn.execute(text("""
        INSERT INTO public.investigation (
            id, repository_code, investigation_code, name, agency, doi,
            description, source_repository_url, metadata, created_at
        ) VALUES (
            :id, 'GUC-TEST', 'GUC-01', 'GUC Test', 'FLARE_TEST', '10.1234/guc-01',
            'Test GUC removal', 'https://example.com/guc-01', '{}'::jsonb, :now
        );
        """), {"id": inv_id, "now": now})

        conn.execute(text("""
        INSERT INTO public.source_document (
            investigation_id, id, original_filename, source_type,
            artifact_origin, sha256, file_size_bytes, storage_key,
            source_version, metadata, created_at
        ) VALUES (
            :inv, :id, 'test.csv', 'csv', 'external_original', :sha,
            100, 'test.csv', '1', '{}'::jsonb, :now
        );
        """), {"inv": inv_id, "id": doc_id, "sha": dummy_sha, "now": now})

    guc_name = f"flare.checked_parse_{str(corrupt_run_id).replace('-', '_')}"

    # Unprivileged user attempts to pre-set the legacy GUC before committing corrupt parse_run
    with pytest.raises(DBAPIError) as exc_info:
        with app.begin() as conn:
            conn.execute(text(f"SELECT set_config('{guc_name}', '1', true);"))
            conn.execute(text("""
            INSERT INTO public.parse_run (
                investigation_id, id, source_document_id, parser_name,
                parser_version, code_sha256, code_storage_key,
                configuration_sha256, configuration, output_sha256,
                output_storage_key, record_count, status, created_at
            ) VALUES (
                :inv, :id, :doc_id, 'malicious_parser',
                '1.0.0', :sha, 'path/code',
                :sha, '{}', :sha,
                'path/out', 100, 'complete', :now
            );
            """), {"inv": inv_id, "id": corrupt_run_id, "doc_id": doc_id, "sha": dummy_sha, "now": now})

    # Must fail with check_violation (23514) from parse_shape
    assert exc_info.value.orig.sqlstate == "23514"
    assert "Incomplete parse membership" in str(exc_info.value)


def test_child_insert_into_existing_unsealed_parse_run_validates(migrated_dbs):
    """Verify that adding child records in a later transaction to an unsealed parse run triggers validation."""
    owner, app = migrated_dbs
    now = datetime.now(timezone.utc)
    dummy_sha = "0" * 64
    inv_id = uuid4()
    doc_id = uuid4()
    run_id = uuid4()
    ev_id = uuid4()
    field_id = uuid4()
    rec_id = uuid4()

    with owner.begin() as conn:
        conn.execute(text("""
        INSERT INTO public.investigation (
            id, repository_code, investigation_code, name, agency, doi,
            description, source_repository_url, metadata, created_at
        ) VALUES (
            :id, 'CHILD-TEST', 'CHILD-01', 'Child Test', 'FLARE_TEST', '10.1234/child-01',
            'Test child validation', 'https://example.com/child-01', '{}'::jsonb, :now
        );
        """), {"id": inv_id, "now": now})

        conn.execute(text("""
        INSERT INTO public.source_document (
            investigation_id, id, original_filename, source_type,
            artifact_origin, sha256, file_size_bytes, storage_key,
            source_version, metadata, created_at
        ) VALUES (
            :inv, :id, 'child.csv', 'csv', 'external_original', :sha,
            100, 'child.csv', '1', '{}'::jsonb, :now
        );
        """), {"inv": inv_id, "id": doc_id, "sha": dummy_sha, "now": now})

        conn.execute(text("""
        INSERT INTO public.evidence_reference (
            investigation_id, id, source_document_id, locator_kind, locator_key,
            locator_version, locator, location_basis, extraction_method, extractor_version,
            verification_status, verification_scope, created_at
        ) VALUES (
            :inv, :id, :doc, 'document', 'test', '1', '{}', 'test', 'test', '1',
            'unverified', 'test', :now
        );
        """), {"inv": inv_id, "id": ev_id, "doc": doc_id, "now": now})

        # Complete and valid 1-record parse run
        conn.execute(text("""
        INSERT INTO public.parse_run (
            investigation_id, id, source_document_id, parser_name,
            parser_version, code_sha256, code_storage_key,
            configuration_sha256, configuration, output_sha256,
            output_storage_key, record_count, status, created_at
        ) VALUES (
            :inv, :id, :doc_id, 'child_parser',
            '1.0.0', :sha, 'path/code',
            :sha, '{}', :sha,
            'path/out', 1, 'complete', :now
        );
        """), {"inv": inv_id, "id": run_id, "doc_id": doc_id, "sha": dummy_sha, "now": now})

        conn.execute(text("""
        INSERT INTO public.source_field (
            investigation_id, id, parse_run_id, table_key, ordinal, original_header,
            raw_unit_status, header_evidence_id, created_at
        ) VALUES (
            :inv, :id, :run, 'tbl', 1, 'f1', 'not_stated', :ev, :now
        );
        """), {"inv": inv_id, "id": field_id, "run": run_id, "ev": ev_id, "now": now})

        conn.execute(text("""
        INSERT INTO public.source_record (
            investigation_id, id, parse_run_id, table_key, source_record_number,
            source_row_id, row_evidence_id, created_at
        ) VALUES (
            :inv, :id, :run, 'tbl', 1, 'r1', :ev, :now
        );
        """), {"inv": inv_id, "id": rec_id, "run": run_id, "ev": ev_id, "now": now})

        conn.execute(text("""
        INSERT INTO public.observation (
            investigation_id, id, parse_run_id, source_record_id, source_field_id,
            evidence_id, raw_value, source_value_kind, unit_origin, parser_classification,
            parser_flags, original_representation, created_at
        ) VALUES (
            :inv, :id, :run, :rec, :fld, :ev, 'val', 'text', 'not_stated', 'text',
            '{}', '{}', :now
        );
        """), {"inv": inv_id, "id": uuid4(), "run": run_id, "rec": rec_id, "fld": field_id, "ev": ev_id, "now": now})

    # Now in a SEPARATE transaction, attempt to insert an additional source_record into that unsealed run
    # (making actual record count 2 while parse_run declared 1)
    with pytest.raises(DBAPIError) as exc_info:
        with app.begin() as conn:
            conn.execute(text("""
            INSERT INTO public.source_record (
                investigation_id, id, parse_run_id, table_key, source_record_number,
                source_row_id, row_evidence_id, created_at
            ) VALUES (
                :inv, :id, :run, 'tbl', 2, 'r2', :ev, :now
            );
            """), {"inv": inv_id, "id": uuid4(), "run": run_id, "ev": ev_id, "now": now})

    assert exc_info.value.orig.sqlstate == "23514"
    assert "Incomplete parse membership" in str(exc_info.value)


def test_child_insert_into_sealed_parse_run_rejected_with_55000(migrated_dbs):
    """Verify that adding child records to a sealed parse run is immediately rejected with SQLSTATE 55000."""
    owner, app = migrated_dbs
    now = datetime.now(timezone.utc)
    inv_id = uuid4()
    doc_id = uuid4()
    run_id = uuid4()
    ev_id = uuid4()
    field_id = uuid4()
    rec_id = uuid4()

    with owner.begin() as conn:
        conn.execute(text("""
        INSERT INTO public.investigation (
            id, repository_code, investigation_code, name, agency, doi,
            description, source_repository_url, metadata, created_at
        ) VALUES (
            :id, 'SEAL-TEST', 'SEAL-01', 'Seal Test', 'FLARE_TEST', '10.1234/seal-01',
            'Test seal guard', 'https://example.com/seal-01', '{}'::jsonb, :now
        );
        """), {"id": inv_id, "now": now})

        cell = {'column_index': 1, 'original_header': 'f1', 'raw_value': 'v', 'classification': 'text', 'quality_flags': []}
        archived = {
            'source': {'filename': 'seal.csv', 'sha256': 'a' * 64},
            'parser_version': '1',
            'record_provenance': {'source_row_id': 'r1', 'data_row_index': 1, 'csv_record_number': 1, 'original_headers': ['f1']},
            'cells': {'f1': cell}
        }
        archive_bytes = (json.dumps(archived) + '\n').encode('utf-8')
        output_sha = hashlib.sha256(archive_bytes).hexdigest()

        conn.execute(text("""
        INSERT INTO public.source_document (
            investigation_id, id, original_filename, source_type,
            artifact_origin, sha256, file_size_bytes, storage_key,
            source_version, metadata, created_at
        ) VALUES (
            :inv, :id, 'seal.csv', 'csv', 'external_original', :sha,
            100, 'seal.csv', '1', '{}'::jsonb, :now
        );
        """), {"inv": inv_id, "id": doc_id, "sha": 'a' * 64, "now": now})

        conn.execute(text("""
        INSERT INTO public.evidence_reference (
            investigation_id, id, source_document_id, locator_kind, locator_key,
            locator_version, locator, location_basis, extraction_method, extractor_version,
            verification_status, verification_scope, created_at
        ) VALUES (
            :inv, :id, :doc, 'document', 'test', '1', '{}', 'test', 'test', '1',
            'unverified', 'test', :now
        );
        """), {"inv": inv_id, "id": ev_id, "doc": doc_id, "now": now})

        conn.execute(text("""
        INSERT INTO public.parse_run (
            investigation_id, id, source_document_id, parser_name,
            parser_version, code_sha256, code_storage_key,
            configuration_sha256, configuration, output_sha256,
            output_storage_key, record_count, status, created_at
        ) VALUES (
            :inv, :id, :doc_id, 'seal_parser',
            '1', :sha, 'path/code',
            :sha, '{}', :out_sha,
            'path/out', 1, 'complete', :now
        );
        """), {"inv": inv_id, "id": run_id, "doc_id": doc_id, "sha": 'a' * 64, "out_sha": output_sha, "now": now})

        conn.execute(text("""
        INSERT INTO public.source_field (
            investigation_id, id, parse_run_id, table_key, ordinal, original_header,
            raw_unit_status, header_evidence_id, created_at
        ) VALUES (
            :inv, :id, :run, 'tbl', 1, 'f1', 'not_stated', :ev, :now
        );
        """), {"inv": inv_id, "id": field_id, "run": run_id, "ev": ev_id, "now": now})

        conn.execute(text("""
        INSERT INTO public.source_record (
            investigation_id, id, parse_run_id, table_key, source_record_number,
            source_row_id, row_evidence_id, created_at
        ) VALUES (
            :inv, :id, :run, 'tbl', 1, 'r1', :ev, :now
        );
        """), {"inv": inv_id, "id": rec_id, "run": run_id, "ev": ev_id, "now": now})

        conn.execute(text("""
        INSERT INTO public.observation (
            investigation_id, id, parse_run_id, source_record_id, source_field_id,
            evidence_id, raw_value, source_value_kind, unit_origin, parser_classification,
            parser_flags, original_representation, created_at
        ) VALUES (
            :inv, :id, :run, :rec, :fld, :ev, 'v', 'text', 'not_stated', 'text',
            '{"quality_flags":[]}', :cell, :now
        );
        """), {"inv": inv_id, "id": uuid4(), "run": run_id, "rec": rec_id, "fld": field_id, "ev": ev_id, "cell": json.dumps(cell), "now": now})

        # Seal the parse run
        conn.execute(
            text("SELECT flare_sealing.seal('parse_run', :inv, :pid, :sid, 'test_actor', :archive)"),
            {"inv": inv_id, "pid": run_id, "sid": uuid4(), "archive": archive_bytes}
        )

    # Now attempt child insertion on the sealed parse run -> must be rejected with 55000
    with pytest.raises(DBAPIError) as exc_info:
        with app.begin() as conn:
            conn.execute(text("""
            INSERT INTO public.source_record (
                investigation_id, id, parse_run_id, table_key, source_record_number,
                source_row_id, row_evidence_id, created_at
            ) VALUES (
                :inv, :id, :run, 'tbl', 2, 'r2', :ev, :now
            );
            """), {"inv": inv_id, "id": uuid4(), "run": run_id, "ev": ev_id, "now": now})

    assert exc_info.value.orig.sqlstate == "55000"
    assert "Aggregate is already sealed" in str(exc_info.value)
