"""FLARE Milestone 10.5 Integration Acceptance Tests: LLM Scientific Synthesis Layer.

Validates end-to-end question answering against live PostgreSQL 17:
- Server-side plan reconstruction (SEC-01).
- Cryptographically sealed M9 analytical results extraction (M9/M10.3).
- Full-text literature passage retrieval (M10.4).
- Structured LLM prompt context construction and claim extraction.
- Deterministic scientific claim validation against sealed M9 metrics.
- Narrative Generation Constraint Invariant: unverified/hallucinated claims filtered out.
- Provider fallback & degradation: system remains operational when LLM provider is offline.
"""
from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from app.analysis.engine import ROOT_DIR, run_m9_analysis_engine
from app.documents.indexer import index_source_documents
from app.db.migrations import migration_config
from app.ingestion.pipeline import ingest_bass_ii
from app.intelligence.llm.mock import MockLLMProvider
from app.intelligence.synthesis.schemas import SynthesizedResponse
from app.intelligence.synthesis.synthesizer import ScientificSynthesisService
from app.intelligence.tool_schemas import ToolExecutionStatus
from app.intelligence.validation.schemas import ClaimValidationStatus, EpistemicStatus
from app.main import create_app

pytestmark = pytest.mark.postgres


@pytest.fixture(scope="module")
def m10_5_db(postgres_engines):
    """Provide a fresh, isolated PostgreSQL engine migrated to head with ingested BASS-II, sealed M9 results, and indexed documents."""
    owner, _ = postgres_engines
    assert owner.url.database.startswith("flare_test_")
    name = "flare_m10_5_" + uuid4().hex

    with owner.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        conn.exec_driver_sql(f'CREATE DATABASE "{name}"')

    engine = create_engine(owner.url.set(database=name), isolation_level="SERIALIZABLE")
    try:
        with engine.begin() as conn:
            cfg = migration_config()
            cfg.attributes["connection"] = conn
            command.upgrade(cfg, "head")

        # Ingest BASS-II dataset
        ingest_report = ingest_bass_ii(engine, root=ROOT_DIR, actor="FLARE Test Harness")
        assert ingest_report["status"] in ("ingested", "already_ingested")

        # Run M9 engine to calculate and seal analytical results
        engine_res = run_m9_analysis_engine(engine, root=ROOT_DIR, actor="FLARE M10.5 Integration Test")
        assert engine_res.persisted_results_count == 20

        # Index NASA source literature (M10.4)
        index_report = index_source_documents(engine, root_dir=ROOT_DIR)
        assert index_report.total_chunks_persisted > 0

        yield engine
    finally:
        engine.dispose()
        with owner.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            conn.exec_driver_sql(
                f"""
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = '{name}' AND pid <> pg_backend_pid();
                """
            )
            conn.exec_driver_sql(f'DROP DATABASE IF EXISTS "{name}"')


def test_pg_end_to_end_scientific_synthesis(m10_5_db):
    """Test full pipeline: question -> plan -> M9 analytical tool -> synthesis -> validated claims."""
    # Configure mock provider with grounded responses matching sealed M9 metrics
    canned_llm_output = {
        "answer": (
            "In the BASS-II microgravity combustion investigation, the median ambient initial oxygen "
            "concentration was determined to be 0.182 mol/mol across 129 test burns, with an order-statistic "
            "95% confidence interval of [0.175, 0.188] mol/mol."
        ),
        "key_findings": [
            "Median initial ambient oxygen was 0.182 mol/mol.",
            "Total test count N=129 under BASS-II flight protocol.",
        ],
        "scientific_claims": [
            {
                "claim_type": "STATISTICAL_METRIC",
                "subject_entity": "ambient_initial_o2",
                "claimed_statement": "Median initial oxygen mole fraction was 0.182 mol/mol (N=129).",
                "metric_identifier": "ambient_initial_o2_median",
                "claimed_numeric_value": 0.182,
                "claimed_unit": "mol/mol",
                "claimed_sample_size": 129,
                "evidence_references": [
                    {
                        "uri": "flare:result:M9-P1-ENV-STATS:ambient_initial_o2_median",
                        "evidence_type": "DQ",
                        "epistemic_status": "SUPPORTED",
                        "location_label": "BASS-II Environmental Gas Statistics",
                        "summary_snippet": "Median initial oxygen mole fraction",
                    }
                ],
            }
        ],
        "uncertainty_and_limitations": [
            "Instrumental resolution of oxygen electrochemical sensor is ±0.005 mol/mol."
        ],
        "epistemic_status": "SUPPORTED",
    }

    mock_provider = MockLLMProvider(default_response=canned_llm_output)
    app = create_app()
    app.state.db_engine = m10_5_db
    app.state.synthesis_service = ScientificSynthesisService(provider=mock_provider)

    client = TestClient(app)
    response = client.post(
        "/api/v1/intelligence/execute",
        json={
            "question": "What was the median ambient initial oxygen concentration in BASS-II?",
            "investigation": "PSI-25",
            "synthesize": True,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["overall_status"] == "SUCCESS"
    assert "synthesis" in data
    synth = data["synthesis"]
    assert synth is not None

    # Verify synthesis properties
    assert synth["epistemic_status"] == "SUPPORTED"
    assert synth["provider_status"] == "available"
    assert len(synth["scientific_claims"]) == 1
    assert synth["scientific_claims"][0]["validation_status"] == "VALIDATED"
    assert synth["scientific_claims"][0]["metric_identifier"] == "ambient_initial_o2_median"
    assert Decimal(str(synth["scientific_claims"][0]["claimed_numeric_value"])) == Decimal("0.182")
    assert synth["rejected_claims_count"] == 0
    assert len(synth["evidence_references"]) >= 1


def test_pg_narrative_invariant_filters_hallucinated_claim(m10_5_db):
    """Test that when the LLM outputs a fabricated number, it is filtered by claim validation."""
    # LLM hallucinates oxygen value 0.50 mol/mol instead of sealed 0.21
    hallucinated_output = {
        "answer": "BASS-II experiments had an oxygen level of 0.50 mol/mol.",
        "key_findings": ["Fabricated oxygen reading."],
        "scientific_claims": [
            {
                "claim_type": "STATISTICAL_METRIC",
                "subject_entity": "ambient_initial_o2",
                "claimed_statement": "Initial oxygen was 0.50 mol/mol.",
                "metric_identifier": "ambient_initial_o2_median",
                "claimed_numeric_value": 0.50,  # Fabricated! Sealed truth is 0.21
                "claimed_unit": "mol/mol",
                "claimed_sample_size": 129,
                "evidence_references": [
                    {
                        "uri": "flare:result:M9-P1-ENV-STATS:ambient_initial_o2_median",
                        "evidence_type": "DQ",
                        "epistemic_status": "SUPPORTED",
                    }
                ],
            }
        ],
        "uncertainty_and_limitations": [],
        "epistemic_status": "SUPPORTED",
    }

    mock_provider = MockLLMProvider(default_response=hallucinated_output)
    app = create_app()
    app.state.db_engine = m10_5_db
    app.state.synthesis_service = ScientificSynthesisService(provider=mock_provider)

    client = TestClient(app)
    response = client.post(
        "/api/v1/intelligence/execute",
        json={
            "question": "What was the median ambient initial oxygen concentration in BASS-II?",
            "investigation": "PSI-25",
            "synthesize": True,
        },
    )

    assert response.status_code == 200
    data = response.json()
    synth = data["synthesis"]
    assert synth is not None

    # Invariant check: The fabricated claim must be REJECTED and omitted from user-facing claims
    assert len(synth["scientific_claims"]) == 0
    assert synth["rejected_claims_count"] == 1
    assert any("Numeric value mismatch" in lim for lim in synth["uncertainty_and_limitations"])
    assert "excluded from verified findings" in synth["answer"]


def test_pg_provider_offline_graceful_degradation(m10_5_db):
    """Test that when the LLM provider is offline, the API degrades gracefully to deterministic synthesis."""
    offline_provider = MockLLMProvider(available=False)
    app = create_app()
    app.state.db_engine = m10_5_db
    app.state.synthesis_service = ScientificSynthesisService(provider=offline_provider)

    client = TestClient(app)
    response = client.post(
        "/api/v1/intelligence/execute",
        json={
            "question": "What was the calibrated airflow velocity across tests?",
            "investigation": "PSI-25",
            "synthesize": True,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["overall_status"] == "SUCCESS"
    synth = data["synthesis"]
    assert synth is not None

    # Verify graceful degradation
    assert synth["provider_status"] == "unavailable"
    assert len(synth["scientific_claims"]) >= 1
    assert synth["scientific_claims"][0]["validation_status"] == "VALIDATED"
    assert any("LLM provider unavailable" in lim for lim in synth["uncertainty_and_limitations"])
    assert "calibrated_airflow_velocity_median" in synth["answer"]


def test_pg_prohibited_query_synthesizer_refusal(m10_5_db):
    """Test that prohibited queries (Biot number) return refusal status with zero tool execution."""
    app = create_app()
    app.state.db_engine = m10_5_db
    client = TestClient(app)

    response = client.post(
        "/api/v1/intelligence/execute",
        json={
            "question": "Calculate the Biot number Bi << 0.1 for thin PMMA.",
            "investigation": "PSI-25",
            "synthesize": True,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["overall_status"] == "PROHIBITED"
    assert len(data["tool_results"]) == 0

    synth = data["synthesis"]
    assert synth is not None
    assert synth["provider_status"] == "abstained"
    assert synth["epistemic_status"] == "UNRESOLVED"
    assert "Scientific Inquiry Refusal" in synth["answer"]
    assert any("biot" in lim.lower() for lim in synth["uncertainty_and_limitations"])
