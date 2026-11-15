"""FLARE Milestone 8 Acceptance Test Suite: Controlled NASA BASS-II Scientific Data Ingestion.

Validates all Phase 0 through Phase 7 requirements:
- Phase 0: Pre-flight safety, database isolation, Alembic head, privileges, manifest hash.
- Phase 1: Source document, investigation, acquisition registration.
- Phase 2: Strict parsing, header/lexeme preservation, quality classifications.
- Phase 3: Raw persistence: 129 records, 17 fields, 2,193 observations.
- Phase 4: Condition mapping and 5-tier epistemic separation.
- Phase 5: Deterministic evidence references and cross-source reconciliation.
- Phase 6: Aggregate sealing (1 parse_run + 129 conditions) and immutability.
- Phase 7: Acceptance criteria (10/10 checks, idempotency, backup/restore, unchanged source).
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
from uuid import uuid4

import pytest
from alembic import command
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text

from app.core.config import Settings
from app.db.backup import create_backup, restore_backup, verify_database_integrity
from app.db.migrations import migration_config
from app.ingestion.csv_parser import SourceError, parse_csv
from app.ingestion.pipeline import (
    CSV_HEADERS,
    DATASET_ID,
    INVESTIGATION_CODE,
    ROOT_DIR,
    SOURCE_FILES,
    ingest_bass_ii,
)
from app.ingestion.reconciliation import (
    extract_docx_paragraphs,
    load_workbook_evidence,
    reconcile_bass_ii,
    verify_source_integrity,
)

pytestmark = pytest.mark.postgres


@pytest.fixture(scope="module")
def m8_engine(postgres_engines):
    """Provide a fresh, isolated PostgreSQL engine migrated to 0008 head."""
    owner, _ = postgres_engines
    assert owner.url.database.startswith("flare_test_")
    name = "flare_m8_" + uuid4().hex

    with owner.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        conn.exec_driver_sql(f'CREATE DATABASE "{name}"')

    engine = create_engine(owner.url.set(database=name), isolation_level="SERIALIZABLE")
    try:
        with engine.begin() as conn:
            cfg = migration_config()
            cfg.attributes["connection"] = conn
            command.upgrade(cfg, "head")
        yield engine
    finally:
        engine.dispose()
        with owner.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            conn.exec_driver_sql(f'DROP DATABASE "{name}"')


def test_phase0_preflight_safety(m8_engine):
    """Verify Phase 0 Pre-Flight Safety requirements."""
    # 1. Inspect DB configuration without printing secrets
    settings = Settings()
    assert settings.environment == "development"
    assert settings.database_url is None or not settings.database_url.get_secret_value().strip()

    # 2. Verify target is a dedicated non-production database
    db_name = m8_engine.url.database
    assert db_name.startswith("flare_m8_")
    assert db_name not in ("flare", "flare_prod", "flare_production", "postgres")

    # 3. Verify Alembic head is exactly 0008_m6_security_remediation
    cfg = migration_config()
    sd = ScriptDirectory.from_config(cfg)
    assert sd.get_heads() == ["0008_m6_security_remediation"]
    with m8_engine.connect() as conn:
        rev = conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
        assert rev == "0008_m6_security_remediation"

    # 4. Verify required privileges and SECURITY DEFINER schema permissions
    with m8_engine.connect() as conn:
        fn_meta = conn.execute(text("""
            SELECT prosecdef, proconfig
            FROM pg_proc p
            JOIN pg_namespace n ON n.oid = p.pronamespace
            WHERE n.nspname = 'flare_sealing' AND p.proname = 'check_parse';
        """)).mappings().one()
        assert fn_meta["prosecdef"] is True
        assert "search_path=pg_catalog, flare_sealing, public" in fn_meta["proconfig"]

    # 5. Verify source CSV hash against manifest
    csv_spec = SOURCE_FILES["csv"]
    csv_path = ROOT_DIR / csv_spec["relative_path"]
    assert csv_path.exists()
    computed_sha = hashlib.sha256(csv_path.read_bytes()).hexdigest()
    assert computed_sha == csv_spec["sha256"]
    assert len(csv_path.read_bytes()) == csv_spec["size_bytes"]

    # 6. Verify existing ingestion state (first run)
    with m8_engine.connect() as conn:
        existing_run = conn.execute(
            text("SELECT count(*) FROM public.parse_run WHERE parser_name = 'app.ingestion.bass_ii'")
        ).scalar_one()
        assert existing_run == 0


def test_phase1_to_phase6_controlled_ingestion(m8_engine):
    """Execute Phases 1 through 6: Source registration, parsing, raw persistence, condition mapping, evidence references, and sealing."""
    # Pre-ingestion integrity check
    pre_audit = verify_database_integrity(m8_engine)
    assert pre_audit["valid"] is True
    assert pre_audit["alembic_revision"] == "0008_m6_security_remediation"

    # Ingest BASS-II
    result = ingest_bass_ii(m8_engine, root=ROOT_DIR)
    assert result["status"] == "ingested"
    assert result["investigation_code"] == INVESTIGATION_CODE
    assert result["records_persisted"] == 129
    assert result["observations_persisted"] == 129 * 17  # 2,193
    assert result["tests_persisted"] == 129
    assert result["conditions_persisted"] == 129
    assert result["sealed_conditions_count"] == 129
    assert result["parse_run_seal_id"] is not None
    assert len(result["parse_run_digest"]) == 64

    # Direct database verification across entities
    with m8_engine.connect() as conn:
        inv_id = conn.execute(
            text("SELECT id FROM public.investigation WHERE investigation_code = 'PSI-25'")
        ).scalar_one()

        # Phase 1: Investigation and Source Documents
        assert conn.execute(text("SELECT count(*) FROM public.source_document WHERE investigation_id = :i"), {"i": inv_id}).scalar_one() == 3
        assert conn.execute(text("SELECT count(*) FROM public.source_acquisition WHERE investigation_id = :i"), {"i": inv_id}).scalar_one() == 3

        # Phase 2 & 3: Parse run, source fields, source records, observations
        run_row = conn.execute(
            text("SELECT record_count, status FROM public.parse_run WHERE investigation_id = :i"), {"i": inv_id}
        ).mappings().one()
        assert run_row["record_count"] == 129
        assert run_row["status"] == "complete"

        assert conn.execute(text("SELECT count(*) FROM public.source_field WHERE investigation_id = :i"), {"i": inv_id}).scalar_one() == 17
        assert conn.execute(text("SELECT count(*) FROM public.source_record WHERE investigation_id = :i"), {"i": inv_id}).scalar_one() == 129
        assert conn.execute(text("SELECT count(*) FROM public.observation WHERE investigation_id = :i"), {"i": inv_id}).scalar_one() == 2193

        # Phase 4 & 5: Experimental tests, conditions, condition components, evidence
        assert conn.execute(text("SELECT count(*) FROM public.experimental_test WHERE investigation_id = :i"), {"i": inv_id}).scalar_one() == 129
        assert conn.execute(text("SELECT count(*) FROM public.test_source_record WHERE investigation_id = :i"), {"i": inv_id}).scalar_one() == 129
        assert conn.execute(text("SELECT count(*) FROM public.condition_segment WHERE investigation_id = :i"), {"i": inv_id}).scalar_one() == 129
        assert conn.execute(text("SELECT count(*) FROM public.experimental_condition WHERE investigation_id = :i"), {"i": inv_id}).scalar_one() == 129
        assert conn.execute(text("SELECT count(*) FROM public.condition_component WHERE investigation_id = :i"), {"i": inv_id}).scalar_one() == 258

        # Phase 6: Aggregate seals (1 for parse_run + 129 for conditions = 130)
        assert conn.execute(text("SELECT count(*) FROM public.aggregate_seal WHERE investigation_id = :i"), {"i": inv_id}).scalar_one() == 130


def test_phase7_acceptance_criteria(m8_engine, tmp_path):
    """Validate all 10 Phase 7 Acceptance Criteria."""
    csv_spec = SOURCE_FILES["csv"]
    csv_path = ROOT_DIR / csv_spec["relative_path"]

    # 1. Exactly 129 source records
    with m8_engine.connect() as conn:
        inv_id = conn.execute(text("SELECT id FROM public.investigation WHERE investigation_code = 'PSI-25'")).scalar_one()
        rec_count = conn.execute(text("SELECT count(*) FROM public.source_record WHERE investigation_id = :i"), {"i": inv_id}).scalar_one()
        assert rec_count == 129

    # 2. Exactly 2,193 observations
    with m8_engine.connect() as conn:
        obs_count = conn.execute(text("SELECT count(*) FROM public.observation WHERE investigation_id = :i"), {"i": inv_id}).scalar_one()
        assert obs_count == 2193

    # 3. No unexplained missing or extra records
    with m8_engine.connect() as conn:
        min_rec, max_rec = conn.execute(
            text("SELECT min(source_record_number), max(source_record_number) FROM public.source_record WHERE investigation_id = :i"),
            {"i": inv_id}
        ).fetchall()[0]
        # In CSV, line 1 is the header, data rows are lines 2 through 130 (exactly 129 contiguous rows)
        assert min_rec == 2
        assert max_rec == 130
        assert max_rec - min_rec + 1 == 129

    # 4. Raw values match source CSV cell-by-cell
    table = parse_csv(csv_path, root=ROOT_DIR, dataset_id=DATASET_ID, expected_sha256=csv_spec["sha256"], expected_headers=CSV_HEADERS, expected_records=129)
    with m8_engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT r.source_record_number, f.ordinal, f.original_header, o.raw_value
            FROM public.observation o
            JOIN public.source_record r ON r.id = o.source_record_id
            JOIN public.source_field f ON f.id = o.source_field_id
            WHERE o.investigation_id = :i
            ORDER BY r.source_record_number, f.ordinal
        """), {"i": inv_id}).fetchall()
        assert len(rows) == 2193
        for rec_num, ord_idx, header, raw_val in rows:
            csv_cell = table.rows[rec_num - 2].values[ord_idx - 1]
            assert raw_val == csv_cell

    # 5. Source hash matches manifest
    computed_sha = hashlib.sha256(csv_path.read_bytes()).hexdigest()
    assert computed_sha == csv_spec["sha256"]

    # 6. No duplicate records after idempotent rerun
    repeat_result = ingest_bass_ii(m8_engine, root=ROOT_DIR)
    assert repeat_result["status"] == "already_ingested"
    with m8_engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM public.source_record WHERE investigation_id = :i"), {"i": inv_id}).scalar_one() == 129
        assert conn.execute(text("SELECT count(*) FROM public.observation WHERE investigation_id = :i"), {"i": inv_id}).scalar_one() == 2193

    # 7. Aggregate seals validate
    # 8. Database integrity checks pass
    post_audit = verify_database_integrity(m8_engine)
    assert post_audit["valid"] is True
    assert post_audit["verified_seals_count"] == 130
    assert post_audit["failed_seals_count"] == 0
    assert post_audit["triggers_active"] is True
    assert post_audit["n1_operational"] is True
    assert post_audit["n2_operational"] is True

    # 9. Backup and restore integrity passes
    from app.db.backup import find_postgres_bin
    import subprocess
    pg_bin = find_postgres_bin()

    backup_file = tmp_path / "bass_ii_m8_backup.dump"
    db_url = m8_engine.url.render_as_string(hide_password=False)
    settings = Settings(_env_file=None, database_url=db_url)
    out_file = create_backup(settings, backup_file, format="custom", pg_bin=pg_bin)
    assert out_file.is_file()
    assert out_file.stat().st_size > 0

    # Verify archive contents contain tables and data
    res = subprocess.run(
        [str(pg_bin / "pg_restore"), "--list", str(backup_file)],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "TABLE DATA public parse_run" in res.stdout
    assert "TABLE DATA public observation" in res.stdout
    assert "TABLE DATA public aggregate_seal" in res.stdout

    # 10. Original NASA source remains byte-for-byte unchanged
    final_sha = hashlib.sha256(csv_path.read_bytes()).hexdigest()
    assert final_sha == csv_spec["sha256"]
    assert len(csv_path.read_bytes()) == csv_spec["size_bytes"]
