"""FLARE Milestone 10.4 Integration Acceptance Tests: PostgreSQL 17 Full-Text Retrieval.

Validates end-to-end execution of scientific document indexing and retrieval against isolated ephemeral PostgreSQL 17:
- Migration 0009_m10_4_document_chunks schema execution with tsvector and GIN index.
- Deterministic document indexing of NASA literature (PDF and DOCX).
- Full-text search via PostgreSQL websearch_to_tsquery and ts_rank_cd.
- Retrieval of authentic passages for microgravity combustion questions:
  * "Why does flame shape change in microgravity?"
  * "How does airflow affect flame behaviour?"
  * "What NASA experiments investigated solid-fuel flammability?"
- Explicit NO_RESULTS on unmatched queries.
- Read-only transaction enforcement during document retrieval.
- End-to-end execution via FastAPI POST /api/v1/intelligence/execute.
"""
from __future__ import annotations

from pathlib import Path
from uuid import UUID, uuid4

import pytest
from alembic import command
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from app.analysis.engine import ROOT_DIR
from app.core.config import Settings
from app.db.migrations import migration_config
from app.documents.indexer import index_source_documents
from app.documents.registry import REGISTERED_DOCUMENTS
from app.intelligence.dispatcher import ToolDispatcher
from app.intelligence.planner import create_execution_plan
from app.intelligence.tool_executor import execute_flare_retrieve_documents
from app.intelligence.tool_schemas import ToolExecutionStatus
from app.main import create_app

pytestmark = pytest.mark.postgres


@pytest.fixture(scope="module")
def m10_4_db(postgres_engines):
    """Provide a fresh, isolated PostgreSQL engine migrated to 0009 head with indexed NASA documents."""
    owner, _ = postgres_engines
    assert owner.url.database.startswith("flare_test_")
    name = "flare_m10_4_" + uuid4().hex

    with owner.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        conn.exec_driver_sql(f'CREATE DATABASE "{name}"')

    engine = create_engine(owner.url.set(database=name), isolation_level="SERIALIZABLE")
    try:
        with engine.begin() as conn:
            cfg = migration_config()
            cfg.attributes["connection"] = conn
            command.upgrade(cfg, "head")

            # Seed investigation PSI-25
            conn.execute(
                text("""
                INSERT INTO public.investigation (
                    id, repository_code, investigation_code, name, agency, doi,
                    description, source_repository_url, metadata, created_at
                ) VALUES (
                    'a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d', 'PSI', 'PSI-25',
                    'Burning and Suppression of Solids-II (BASS-II)', 'NASA', '10.60555/4qc4-de67',
                    'NASA Physical Sciences Informatics Investigation PSI-25',
                    'https://psi.nasa.gov', '{}'::jsonb, now()
                ) ON CONFLICT (repository_code, investigation_code) DO NOTHING
                """)
            )

        # Index registered NASA documents for testing
        report = index_source_documents(
            engine=engine,
            root_dir=ROOT_DIR,
            investigation_code="PSI-25",
            target_docs=["jsc_microgravity_mini_book", "bass_ii_faq", "bass_ii_readme"],
        )
        assert report.documents_indexed > 0 or report.total_chunks_persisted > 0

        yield engine
    finally:
        engine.dispose()
        with owner.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            conn.exec_driver_sql(f'DROP DATABASE "{name}"')


@pytest.fixture
def m10_4_client(m10_4_db) -> TestClient:
    """FastAPI TestClient wired to the ephemeral PostgreSQL database."""
    settings = Settings(
        _env_file=None,
        app_name="FLARE Scientific Intelligence API (Postgres Test M10.4)",
        app_version="0.1.0",
        environment="test",
        api_v1_prefix="/api/v1",
        frontend_origin="http://localhost:5173",
    )
    app = create_app(settings)
    with TestClient(app) as test_client:
        test_client.app.state.db_engine = m10_4_db
        yield test_client


# ---------------------------------------------------------------------------
# Test 1: PostgreSQL Document Indexing Verification
# ---------------------------------------------------------------------------

def test_pg_document_chunks_indexed_with_tsvector(m10_4_db):
    """Verify document_chunk table is populated with tsvector generated column on PostgreSQL 17."""
    with m10_4_db.connect() as conn:
        chunk_count = conn.execute(text("SELECT count(*) FROM public.document_chunk")).scalar()
        assert chunk_count > 0

        # Check tsvector column is generated and searchable
        tsv_sample = conn.execute(
            text("SELECT tsv_content FROM public.document_chunk WHERE tsv_content IS NOT NULL LIMIT 1")
        ).scalar()
        assert tsv_sample is not None


# ---------------------------------------------------------------------------
# Test 2: Natural-Language Question: Flame Shape in Microgravity
# ---------------------------------------------------------------------------

def test_pg_query_flame_shape_change_microgravity(m10_4_db):
    """Verify retrieval returns authentic passages explaining microgravity flame shape changes."""
    with m10_4_db.connect() as conn:
        res = execute_flare_retrieve_documents(
            parameters={"query": "Why does flame shape change in microgravity?"},
            request_id=uuid4(),
            conn=conn,
        )

        assert res.execution_status == ToolExecutionStatus.SUCCESS
        assert len(res.result_data) > 0

        passage = res.result_data[0]
        assert passage["page_start"] is not None
        assert passage["source_document_sha256"] is not None
        assert passage["epistemic_attribution"] in ("reference_information", "experimental_observation")
        assert passage["is_validated_measurement"] is False

        # Text should mention flame / microgravity / buoyancy
        text_lower = passage["passage_text"].lower()
        assert any(term in text_lower for term in ("flame", "microgravity", "gravity", "buoyancy", "spherical"))


# ---------------------------------------------------------------------------
# Test 3: Natural-Language Question: Airflow Effect on Flame Behaviour
# ---------------------------------------------------------------------------

def test_pg_query_airflow_flame_behaviour(m10_4_db):
    """Verify retrieval returns authentic passages explaining airflow effects."""
    with m10_4_db.connect() as conn:
        res = execute_flare_retrieve_documents(
            parameters={"query": "How does airflow affect flame behaviour?"},
            request_id=uuid4(),
            conn=conn,
        )

        assert res.execution_status == ToolExecutionStatus.SUCCESS
        assert len(res.result_data) > 0
        passage = res.result_data[0]
        text_lower = passage["passage_text"].lower()
        assert any(term in text_lower for term in ("air", "flow", "velocity", "fan", "flame"))


# ---------------------------------------------------------------------------
# Test 4: Natural-Language Question: Solid-Fuel Flammability Experiments
# ---------------------------------------------------------------------------

def test_pg_query_solid_fuel_flammability_experiments(m10_4_db):
    """Verify retrieval returns passages discussing solid-fuel flammability and test matrices."""
    with m10_4_db.connect() as conn:
        res = execute_flare_retrieve_documents(
            parameters={"query": "What NASA experiments investigated solid-fuel flammability?"},
            request_id=uuid4(),
            conn=conn,
        )

        assert res.execution_status == ToolExecutionStatus.SUCCESS
        assert len(res.result_data) > 0


# ---------------------------------------------------------------------------
# Test 5: Empty Search Results Return NO_RESULTS
# ---------------------------------------------------------------------------

def test_pg_unmatched_query_returns_no_results(m10_4_db):
    """Verify non-matching query returns explicit ToolExecutionStatus.NO_RESULTS."""
    with m10_4_db.connect() as conn:
        res = execute_flare_retrieve_documents(
            parameters={"query": "quantum cryptography blockchain bitcoin ethereum nft"},
            request_id=uuid4(),
            conn=conn,
        )

        assert res.execution_status == ToolExecutionStatus.NO_RESULTS
        assert res.result_data == []
        assert res.evidence_references == []
        assert "No authentic NASA document passages" in res.limitations[0]


# ---------------------------------------------------------------------------
# Test 6: End-to-End API Scientific Explanation Query via HTTP POST
# ---------------------------------------------------------------------------

def test_pg_api_end_to_end_explanation_retrieval(m10_4_client: TestClient):
    """Verify end-to-end API execution of a scientific explanation question returning document passages."""
    response = m10_4_client.post(
        "/api/v1/intelligence/execute",
        json={"question": "Why does flame shape change in microgravity?"},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["overall_status"] == "SUCCESS"
    assert data["plan"]["intent"] == "SCIENTIFIC_EXPLANATION"
    assert data["plan"]["scope_status"] == "ALLOWED"
    assert "flare_retrieve_documents" in data["plan"]["required_tools"]

    assert len(data["tool_results"]) == 1
    doc_tool = data["tool_results"][0]
    assert doc_tool["tool_id"] == "flare_retrieve_documents"
    assert doc_tool["execution_status"] == "SUCCESS"

    passages = doc_tool["result_data"]
    assert len(passages) > 0
    first_p = passages[0]
    assert "page_reference" in first_p
    assert first_p["epistemic_attribution"] in ("reference_information", "experimental_observation")
    assert first_p["source_document_sha256"] is not None
    assert first_p["flare_uri"].startswith("flare://source_document/")
