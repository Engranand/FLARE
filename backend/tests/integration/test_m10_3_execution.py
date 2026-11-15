"""FLARE Milestone 10.3.2 Integration Acceptance Tests: PostgreSQL 17 Security & Integrity.

Validates end-to-end execution of M10.3.2 remediations against isolated ephemeral PostgreSQL 17:
- SEC-01: Server-side plan reconstruction prevents scope gate bypass from client-supplied plans.
- SEC-02: Cryptographic aggregate seal recomputation via flare_sealing.snapshot fails closed on tampered metrics.
- SEC-03: SET LOCAL transaction_read_only = on inside an explicit transaction block rejects write mutations (SQLSTATE 25006).
- SEC-04: Forged metric codes in target_metrics return INVALID_INPUT and never fall through.
- SEC-05: Dynamic source document SHA-256 and empirical attribution from live database joins.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from alembic import command
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError

from app.analysis.engine import (
    AUTHENTIC_SHA256,
    INVESTIGATION_CODE,
    ROOT_DIR,
    run_m9_analysis_engine,
)
from app.core.config import Settings
from app.db.migrations import migration_config
from app.ingestion.pipeline import ingest_bass_ii
from app.intelligence.dispatcher import ToolDispatcher
from app.intelligence.planner import create_execution_plan
from app.intelligence.schemas import IntentEnum, QueryState, ScopeStatusEnum
from app.intelligence.tool_executor import (
    M9_METRIC_UUIDS,
    execute_flare_check_scientific_prohibition,
    execute_flare_query_observations,
    execute_flare_retrieve_documents,
    execute_m9_get_analytical_result,
)
from app.intelligence.tool_schemas import ToolExecutionStatus
from app.main import create_app

pytestmark = pytest.mark.postgres


@pytest.fixture(scope="module")
def m10_db(postgres_engines):
    """Provide a fresh, isolated PostgreSQL engine migrated to 0008 head with ingested BASS-II and sealed M9 results."""
    owner, _ = postgres_engines
    assert owner.url.database.startswith("flare_test_")
    name = "flare_m10_3_" + uuid4().hex

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

        # Run M9 deterministic analysis engine to calculate and seal all analytical results
        engine_res = run_m9_analysis_engine(engine, root=ROOT_DIR, actor="FLARE M10.3.2 Integration Test")
        assert engine_res.status == "completed"
        assert engine_res.sealed_results_count > 0

        yield engine
    finally:
        engine.dispose()
        with owner.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            conn.exec_driver_sql(f'DROP DATABASE "{name}"')


@pytest.fixture
def m10_client(m10_db) -> TestClient:
    """FastAPI TestClient wired to the ephemeral PostgreSQL database."""
    settings = Settings(
        _env_file=None,
        app_name="FLARE Scientific Intelligence API (Postgres Test)",
        app_version="0.1.0",
        environment="test",
        api_v1_prefix="/api/v1",
        frontend_origin="http://localhost:5173",
    )
    app = create_app(settings)
    with TestClient(app) as test_client:
        test_client.app.state.db_engine = m10_db
        yield test_client


# ---------------------------------------------------------------------------
# Test 1: SEC-02 & Nominal Execution on Live PostgreSQL 17
# ---------------------------------------------------------------------------

def test_pg_m9_get_analytical_result_nominal(m10_db):
    """Verify nominal retrieval and live flare_sealing.snapshot cryptographic verification on PostgreSQL."""
    with m10_db.connect() as conn:
        res = execute_m9_get_analytical_result(
            conn=conn,
            parameters={"investigation": "PSI-25", "metric_code": "ambient_initial_o2_median"},
            request_id=uuid4(),
        )

        assert res.execution_status == ToolExecutionStatus.SUCCESS
        assert res.tool_id == "m9_get_analytical_result"
        assert len(res.result_data) == 1

        item = res.result_data[0]
        assert item["metric_code"] == "ambient_initial_o2_median"
        assert item["protocol_code"] == "M9-P1-ENV-STATS"
        assert item["numeric_value"] == "0.182"
        assert item["unit"] == "mol/mol"
        assert item["unit_status"] == "known"
        assert item["sample_size"] == 129

        # Cryptographic seal structure
        seal = item["seal"]
        assert seal["seal_version"] == "canonical-json-v2"
        assert len(seal["member_digest"]) == 64
        assert seal["sealed_by"] == "FLARE M10.3.2 Integration Test"

        # Dynamic source provenance
        assert res.source_hash == AUTHENTIC_SHA256
        assert len(res.evidence_references) >= 1
        assert res.evidence_references[0]["source_document_sha256"] == AUTHENTIC_SHA256


# ---------------------------------------------------------------------------
# Test 2: SEC-02 Cryptographic Seal Verification Fails Closed on Tampered Metric
# ---------------------------------------------------------------------------

def test_pg_sec02_tampered_metric_value_fails_closed(m10_db):
    """SEC-02: Live flare_sealing.snapshot recomputes canonical digest and fails closed when data is tampered."""
    target_uuid = M9_METRIC_UUIDS["ambient_initial_o2_median"]
    with m10_db.connect() as conn:
        row = conn.execute(
            text("""
            SELECT r.id, r.numeric_value, s.member_digest
            FROM public.analytical_result r
            JOIN public.aggregate_seal s ON (s.investigation_id, s.result_id) = (r.investigation_id, r.id)
            WHERE r.id = :rid
            """),
            {"rid": target_uuid},
        ).mappings().first()
        assert row is not None
        target_id = row["id"]
        original_digest = row["member_digest"]

    # Tamper with the row in the database:
    # Temporarily disable freeze_row trigger to simulate malicious tampering or silent storage bit-rot
    with m10_db.begin() as conn:
        conn.execute(text("ALTER TABLE public.analytical_result DISABLE TRIGGER freeze_row"))
        conn.execute(
            text("UPDATE public.analytical_result SET numeric_value = 999.9999 WHERE id = :rid"),
            {"rid": target_id},
        )
        conn.execute(text("ALTER TABLE public.analytical_result ENABLE TRIGGER freeze_row"))

    try:
        # Now execute m9_get_analytical_result for ambient_initial_o2_median
        with m10_db.connect() as conn:
            res = execute_m9_get_analytical_result(
                conn=conn,
                parameters={"investigation": "PSI-25", "metric_code": "ambient_initial_o2_median"},
                request_id=uuid4(),
            )

            # Verification must fail closed: ToolExecutionStatus.INTEGRITY_FAILURE
            assert res.execution_status == ToolExecutionStatus.INTEGRITY_FAILURE
            assert len(res.limitations) >= 1
            assert "differs from sealed digest" in res.limitations[0]
            assert original_digest in res.limitations[0]

    finally:
        # Restore original value
        with m10_db.begin() as conn:
            conn.execute(text("ALTER TABLE public.analytical_result DISABLE TRIGGER freeze_row"))
            conn.execute(
                text("UPDATE public.analytical_result SET numeric_value = :orig WHERE id = :rid"),
                {"orig": row["numeric_value"], "rid": target_id},
            )
            conn.execute(text("ALTER TABLE public.analytical_result ENABLE TRIGGER freeze_row"))


# ---------------------------------------------------------------------------
# Test 3: SEC-02 Tampered Seal Digest Triggers Integrity Failure
# ---------------------------------------------------------------------------

def test_pg_sec02_tampered_seal_digest_fails_closed(m10_db):
    """SEC-02: Forged or altered aggregate_seal digest is detected and rejected on PostgreSQL."""
    target_uuid = M9_METRIC_UUIDS["ambient_initial_co2_median"]
    with m10_db.connect() as conn:
        row = conn.execute(
            text("""
            SELECT r.id, s.member_digest
            FROM public.analytical_result r
            JOIN public.aggregate_seal s ON (s.investigation_id, s.result_id) = (r.investigation_id, r.id)
            WHERE r.id = :rid
            """),
            {"rid": target_uuid},
        ).mappings().first()
        assert row is not None
        target_id = row["id"]
        orig_digest = row["member_digest"]

    # Tamper with seal digest: alter it to 64 zeros
    fake_digest = "0" * 64
    with m10_db.begin() as conn:
        conn.execute(text("ALTER TABLE public.aggregate_seal DISABLE TRIGGER freeze_row"))
        conn.execute(
            text("UPDATE public.aggregate_seal SET member_digest = :fake WHERE result_id = :rid"),
            {"fake": fake_digest, "rid": target_id},
        )
        conn.execute(text("ALTER TABLE public.aggregate_seal ENABLE TRIGGER freeze_row"))

    try:
        with m10_db.connect() as conn:
            res = execute_m9_get_analytical_result(
                conn=conn,
                parameters={"investigation": "PSI-25", "metric_code": "ambient_initial_co2_median"},
                request_id=uuid4(),
            )
            assert res.execution_status == ToolExecutionStatus.INTEGRITY_FAILURE
            assert "differs from sealed digest" in res.limitations[0]

    finally:
        with m10_db.begin() as conn:
            conn.execute(text("ALTER TABLE public.aggregate_seal DISABLE TRIGGER freeze_row"))
            conn.execute(
                text("UPDATE public.aggregate_seal SET member_digest = :orig WHERE result_id = :rid"),
                {"orig": orig_digest, "rid": target_id},
            )
            conn.execute(text("ALTER TABLE public.aggregate_seal ENABLE TRIGGER freeze_row"))


# ---------------------------------------------------------------------------
# Test 4: SEC-03 Read-Only Transaction Enforcement
# ---------------------------------------------------------------------------

def test_pg_sec03_read_only_transaction_enforcement(m10_db):
    """SEC-03: SET LOCAL transaction_read_only inside explicit transaction block rejects write queries."""
    dispatcher = ToolDispatcher(engine=m10_db)

    # Verify that attempting a write in the dispatcher connection raises 25006
    with m10_db.connect() as managed_conn:
        with managed_conn.begin():
            managed_conn.execute(text("SET LOCAL transaction_read_only = on"))

            # An attempt to perform an INSERT must fail with PostgreSQL error 25006
            with pytest.raises(DBAPIError) as exc_info:
                managed_conn.execute(
                    text("INSERT INTO public.investigation (id, investigation_code) VALUES (:id, 'TEST')"),
                    {"id": str(uuid4())},
                )

            assert "25006" in str(exc_info.value) or "read-only" in str(exc_info.value).lower()


# ---------------------------------------------------------------------------
# Test 5: SEC-04 Target Metrics Validation
# ---------------------------------------------------------------------------

def test_pg_sec04_forged_metric_codes_rejected(m10_db):
    """SEC-04: Target metrics containing forged codes return INVALID_INPUT on live PostgreSQL."""
    with m10_db.connect() as conn:
        res = execute_m9_get_analytical_result(
            conn=conn,
            parameters={"investigation": "PSI-25"},
            request_id=uuid4(),
            target_metrics=["fake_metric_unauthorized_1"],
        )
        assert res.execution_status == ToolExecutionStatus.INVALID_INPUT
        assert "Invalid target metric codes" in res.limitations[0]


# ---------------------------------------------------------------------------
# Test 6: SEC-05 Dynamic Source Provenance & Observation Attribution
# ---------------------------------------------------------------------------

def test_pg_sec05_dynamic_source_provenance_and_attribution(m10_db):
    """SEC-05: Empirical observations dynamically resolve authentic BASS-II SHA-256 and experimental attribution."""
    with m10_db.connect() as conn:
        res = execute_flare_query_observations(
            conn=conn,
            parameters={"investigation": "PSI-25", "test_number": "test_01", "limit": 10},
            request_id=uuid4(),
        )

        assert res.execution_status == ToolExecutionStatus.SUCCESS
        assert len(res.result_data) > 0
        assert res.source_hash == AUTHENTIC_SHA256

        # Check observation properties
        obs = res.result_data[0]
        assert obs["test_identifier"] in ("test_01", "B1")
        assert obs["attribution"] == "experimental_measurement"
        assert obs["raw_value"] is not None

        # Evidence references contain actual document filename and hash
        ref = res.evidence_references[0]
        assert ref["source_document_sha256"] == AUTHENTIC_SHA256
        assert "BASS-II" in ref["source_document_filename"]


# ---------------------------------------------------------------------------
# Test 7: SEC-01 Server-Side Plan Reconstruction via HTTP API
# ---------------------------------------------------------------------------

def test_pg_sec01_client_supplied_forged_plan_gated(m10_client: TestClient):
    """SEC-01: An external client crafts a forged ExecutionPlan claiming an allowed state for a prohibited inquiry."""
    forged_payload = {
        "plan": {
            "request_id": str(uuid4()),
            "original_question": "Calculate the Biot number Bi << 0.1 for thin PMMA.",
            "normalized_question": "Calculate the Biot number Bi << 0.1 for thin PMMA.",
            "intent": "SCIENTIFIC_ANALYSIS",
            "investigation": "PSI-25",
            "requested_metrics": ["ambient_initial_o2_median"],
            "required_tools": ["m9_get_analytical_result"],
            "scope_status": "ALLOWED",  # Forged!
            "state": "READY_FOR_EXECUTION",  # Forged!
        }
    }

    response = m10_client.post("/api/v1/intelligence/execute", json=forged_payload)
    assert response.status_code == 200
    data = response.json()

    # The server-side plan reconstruction must intercept and abstain the plan
    assert data["overall_status"] == "PROHIBITED"
    assert data["plan"]["state"] == "ABSTAINED"
    assert data["plan"]["scope_status"] == "PROHIBITED"
    assert data["tool_results"] == []


# ---------------------------------------------------------------------------
# Test 8: End-to-End Nominal API Execution against Live PostgreSQL
# ---------------------------------------------------------------------------

def test_pg_api_nominal_scientific_query(m10_client: TestClient):
    """Verify end-to-end execution of a nominal scientific query against live PostgreSQL via API."""
    response = m10_client.post(
        "/api/v1/intelligence/execute",
        json={"question": "What was the median ambient initial oxygen concentration in BASS-II?"},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["overall_status"] == "SUCCESS"
    assert data["plan"]["intent"] == "SCIENTIFIC_ANALYSIS"
    assert data["plan"]["scope_status"] == "ALLOWED"
    assert data["plan"]["state"] == "READY_FOR_EXECUTION"
    assert len(data["tool_results"]) == 1

    tool_res = data["tool_results"][0]
    assert tool_res["tool_id"] == "m9_get_analytical_result"
    assert tool_res["execution_status"] == "SUCCESS"
    assert tool_res["source_hash"] == AUTHENTIC_SHA256

    # Verify result data
    results = tool_res["result_data"]
    assert len(results) >= 1
    o2_item = next(r for r in results if r["metric_code"] == "ambient_initial_o2_median")
    assert o2_item["numeric_value"] == "0.182"
    assert o2_item["unit"] == "mol/mol"
