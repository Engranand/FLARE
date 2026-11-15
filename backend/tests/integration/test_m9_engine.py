"""FLARE Milestone 9 Integration Acceptance Tests: Deterministic Scientific Analysis Engine.

Validates end-to-end execution of M9 on isolated ephemeral PostgreSQL 17:
- Seeding and cryptographic sealing of analysis protocols.
- Execution of pure-Python calculation modules (P1, P2, P3, P4).
- Database persistence of analytical_result and result_evidence rows.
- Cryptographic aggregate sealing of analytical results via flare_sealing.seal.
- Idempotency of engine execution (duplicate run preserves seals).
- Database immutability triggers on sealed analytical results.
- Service and query layer verification.
"""
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from alembic import command
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError

from app.analysis.engine import (
    AUTHENTIC_SHA256,
    INVESTIGATION_CODE,
    ROOT_DIR,
    run_m9_analysis_engine,
)
from app.analysis.protocols import PROTOCOL_SPECS
from app.db.migrations import migration_config
from app.ingestion.pipeline import ingest_bass_ii
from app.services.analysis import (
    get_analysis_protocols_service,
    get_analysis_results_service,
)

pytestmark = pytest.mark.postgres


@pytest.fixture(scope="module")
def m9_db(postgres_engines):
    """Provide a fresh, isolated PostgreSQL engine migrated to 0008 head with ingested BASS-II."""
    owner, _ = postgres_engines
    assert owner.url.database.startswith("flare_test_")
    name = "flare_m9_" + uuid4().hex

    with owner.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        conn.exec_driver_sql(f'CREATE DATABASE "{name}"')

    engine = create_engine(owner.url.set(database=name), isolation_level="SERIALIZABLE")
    try:
        with engine.begin() as conn:
            cfg = migration_config()
            cfg.attributes["connection"] = conn
            command.upgrade(cfg, "head")

        # Ingest BASS-II dataset once for the test module
        ingest_report = ingest_bass_ii(engine, root=ROOT_DIR, actor="FLARE Test Harness")
        assert ingest_report["status"] in ("ingested", "already_ingested")
        yield engine
    finally:
        engine.dispose()
        with owner.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            conn.exec_driver_sql(f'DROP DATABASE "{name}"')


def test_m9_engine_execution_and_persistence(m9_db):
    """Test full execution of M9 analysis engine, metric calculation, and DB persistence."""
    result = run_m9_analysis_engine(m9_db, root=ROOT_DIR, actor="FLARE M9 Integration Test")

    assert result.status == "completed"
    assert result.investigation_code == INVESTIGATION_CODE
    assert result.source_sha256 == AUTHENTIC_SHA256
    assert result.total_metrics_computed > 0
    assert result.persisted_results_count == result.total_metrics_computed
    assert result.sealed_results_count == result.persisted_results_count

    # Verify all 4 modules reported
    assert "P1_ENV_STATS" in result.module_reports
    assert "P2_O2_DEPLETION" in result.module_reports
    assert "P3_AIRFLOW_STEADY" in result.module_reports
    assert "P4_FUEL_REGIMES" in result.module_reports


def test_m9_protocols_seeded_and_sealed(m9_db):
    """Verify that all 4 analysis protocols are present in DB and cryptographically sealed."""
    protocols = get_analysis_protocols_service(m9_db)
    codes = {p["protocol_code"] for p in protocols}

    for spec in PROTOCOL_SPECS:
        assert spec["code"] in codes

    with m9_db.connect() as conn:
        for spec in PROTOCOL_SPECS:
            p_code = spec["code"]
            prot_row = conn.execute(
                text("""
                SELECT p.id, s.id AS seal_id, s.member_digest
                FROM public.analysis_protocol p
                JOIN public.aggregate_seal s ON (s.investigation_id = p.investigation_id AND s.protocol_id = p.id)
                WHERE p.protocol_code = :pcode
                """),
                {"pcode": p_code},
            ).mappings().first()

            assert prot_row is not None, f"Protocol {p_code} is not sealed!"
            assert prot_row["seal_id"] is not None
            assert len(prot_row["member_digest"]) == 64


def test_m9_analytical_results_sealed_and_immutable(m9_db):
    """Verify that every analytical result has a valid cryptographic seal and is immutable."""
    results = get_analysis_results_service(m9_db)
    assert len(results) > 0

    with m9_db.connect() as conn:
        for r in results:
            res_id = r["id"]
            # 1. Check seal exists in aggregate_seal
            seal_row = conn.execute(
                text("""
                SELECT id, member_digest, member_counts, seal_version
                FROM public.aggregate_seal
                WHERE result_id = :rid
                """),
                {"rid": res_id},
            ).mappings().first()

            assert seal_row is not None, f"Result {res_id} has no seal!"
            assert seal_row["seal_version"] == "canonical-json-v2"
            assert len(seal_row["member_digest"]) == 64

            # 2. Check child evidence exists
            ev_count = conn.execute(
                text("SELECT count(*) FROM public.result_evidence WHERE result_id = :rid"),
                {"rid": res_id},
            ).scalar_one()
            assert ev_count >= 1

    # 3. Test immutability: attempting to update a sealed analytical result must fail
    target_res = results[0]["id"]
    with pytest.raises(DBAPIError) as exc_info:
        with m9_db.begin() as conn:
            conn.execute(
                text("UPDATE public.analytical_result SET producer_ref = 'tampered' WHERE id = :rid"),
                {"rid": target_res},
            )
    assert "immutable" in str(exc_info.value).lower() or "frozen" in str(exc_info.value).lower()


def test_m9_engine_idempotency(m9_db):
    """Verify that re-executing M9 analysis engine is completely idempotent."""
    # First get existing results and seal digests
    initial_results = get_analysis_results_service(m9_db)
    initial_digests = {str(r["id"]): r["seal_digest"] for r in initial_results}

    # Run engine again
    second_run = run_m9_analysis_engine(m9_db, root=ROOT_DIR, actor="FLARE M9 Idempotency Test")
    assert second_run.status == "completed"

    # Query results again
    after_results = get_analysis_results_service(m9_db)
    assert len(after_results) == len(initial_results)

    after_digests = {str(r["id"]): r["seal_digest"] for r in after_results}
    # All cryptographic seal digests must be identical
    assert after_digests == initial_digests
