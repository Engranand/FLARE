"""Comprehensive test suite for FLARE Milestone 10.3 Scientific Tool Execution Layer.

Covers:
1. m9_get_analytical_result execution & verification (valid metrics, invalid codes, seal checks, integrity failures)
2. flare_query_observations execution & verification (test ID, variable filters, attribution, row limits, SQL injection safety)
3. flare_check_scientific_prohibition execution & verification (prohibitions, allowed concepts)
4. flare_retrieve_documents contract (NOT_IMPLEMENTED status in M10.3)
5. ToolDispatcher orchestration (deadlines, read-only boundaries, rollback, status aggregation)
6. API endpoint POST /api/v1/intelligence/execute
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
import json
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, text
from sqlalchemy.pool import StaticPool

from app.core.config import Settings
from app.intelligence.dispatcher import ToolDispatcher
from app.intelligence.planner import create_execution_plan
from app.intelligence.schemas import ExecutionPlan, IntentEnum, QueryState, ScopeStatusEnum
from app.intelligence.tool_executor import (
    AUTHENTIC_BASS_II_SHA256,
    M9_PROTOCOL_CODES,
    execute_flare_check_scientific_prohibition,
    execute_flare_query_observations,
    execute_flare_retrieve_documents,
    execute_m9_get_analytical_result,
)
from app.intelligence.tool_schemas import (
    ExecutionRequest,
    ExecutionResponse,
    ToolExecutionStatus,
    ToolResult,
)
from app.main import create_app


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client() -> TestClient:
    settings = Settings(
        _env_file=None,
        app_name="FLARE Scientific Intelligence API",
        app_version="0.1.0",
        environment="test",
        api_v1_prefix="/api/v1",
        frontend_origin="http://localhost:5173",
    )
    with TestClient(create_app(settings)) as test_client:
        yield test_client


@pytest.fixture
def mock_db_engine():
    """Create a persistent in-memory SQLite engine with 'public' schema populated for unit tests."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def attach_public(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("ATTACH DATABASE ':memory:' AS public")
        cursor.close()

    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE public.investigation (
                id TEXT PRIMARY KEY,
                investigation_code TEXT UNIQUE NOT NULL
            )
        """))
        conn.execute(text("""
            CREATE TABLE public.analysis_protocol (
                investigation_id TEXT,
                id TEXT PRIMARY KEY,
                protocol_code TEXT NOT NULL,
                protocol_version TEXT NOT NULL,
                description TEXT
            )
        """))
        conn.execute(text("""
            CREATE TABLE public.analytical_result (
                investigation_id TEXT,
                id TEXT PRIMARY KEY,
                protocol_id TEXT,
                method TEXT,
                method_version TEXT,
                result_kind TEXT,
                numeric_value REAL,
                unit TEXT,
                unit_status TEXT,
                text_value TEXT,
                parameters TEXT,
                uncertainty TEXT,
                producer_ref TEXT,
                created_at TIMESTAMP
            )
        """))
        conn.execute(text("""
            CREATE TABLE public.aggregate_seal (
                investigation_id TEXT,
                id TEXT PRIMARY KEY,
                result_id TEXT,
                seal_version TEXT,
                member_counts TEXT,
                member_digest TEXT,
                sealed_by TEXT,
                created_at TIMESTAMP
            )
        """))
        conn.execute(text("""
            CREATE TABLE public.source_document (
                investigation_id TEXT,
                id TEXT PRIMARY KEY,
                sha256 TEXT,
                original_filename TEXT
            )
        """))
        conn.execute(text("""
            CREATE TABLE public.evidence_reference (
                investigation_id TEXT,
                id TEXT PRIMARY KEY,
                source_document_id TEXT
            )
        """))
        conn.execute(text("""
            CREATE TABLE public.result_evidence (
                investigation_id TEXT,
                id TEXT PRIMARY KEY,
                result_id TEXT,
                evidence_id TEXT,
                role TEXT
            )
        """))
        conn.execute(text("""
            CREATE TABLE public.parse_run (
                investigation_id TEXT,
                id TEXT PRIMARY KEY,
                source_document_id TEXT
            )
        """))
        conn.execute(text("""
            CREATE TABLE public.source_record (
                investigation_id TEXT,
                id TEXT PRIMARY KEY,
                parse_run_id TEXT,
                source_record_number INTEGER,
                source_row_id TEXT
            )
        """))
        conn.execute(text("""
            CREATE TABLE public.source_field (
                investigation_id TEXT,
                id TEXT PRIMARY KEY,
                parse_run_id TEXT,
                ordinal INTEGER,
                original_header TEXT,
                raw_unit TEXT
            )
        """))
        conn.execute(text("""
            CREATE TABLE public.observation (
                investigation_id TEXT,
                id TEXT PRIMARY KEY,
                parse_run_id TEXT,
                source_record_id TEXT,
                source_field_id TEXT,
                raw_value TEXT,
                source_value_kind TEXT,
                raw_unit TEXT,
                parser_classification TEXT,
                parser_flags TEXT
            )
        """))
        conn.execute(text("""
            CREATE TABLE public.experimental_test (
                investigation_id TEXT,
                id TEXT PRIMARY KEY,
                test_identifier TEXT
            )
        """))
        conn.execute(text("""
            CREATE TABLE public.test_source_record (
                investigation_id TEXT,
                id TEXT PRIMARY KEY,
                experimental_test_id TEXT,
                source_record_id TEXT
            )
        """))
        conn.execute(text("""
            CREATE TABLE public.semantic_annotation (
                investigation_id TEXT,
                id TEXT PRIMARY KEY,
                observation_id TEXT,
                variable_id TEXT,
                numeric_value REAL,
                interpreted_unit TEXT
            )
        """))
        conn.execute(text("""
            CREATE TABLE public.scientific_variable (
                investigation_id TEXT,
                id TEXT PRIMARY KEY,
                variable_code TEXT
            )
        """))

        # Seed minimal authentic data
        inv_id = str(uuid4())
        doc_id = str(uuid4())
        pr_id = str(uuid4())
        prot_id = str(uuid4())
        res_id = str(uuid4())
        seal_id = str(uuid4())
        ev_id = str(uuid4())
        test_id = str(uuid4())
        sr_id = str(uuid4())
        sf_id = str(uuid4())
        obs_id = str(uuid4())

        now = datetime.now(timezone.utc).isoformat()
        dummy_sha = "71e792bf6b5fb5ea620c5dd70fbbac05515992e12aefcf5dff47312caa48c042"

        conn.execute(text("INSERT INTO public.investigation VALUES (:id, 'PSI-25')"), {"id": inv_id})
        conn.execute(text("INSERT INTO public.source_document VALUES (:inv, :id, :sha, 'PSI-25_Experimental table_BASS-II.csv')"),
                     {"inv": inv_id, "id": doc_id, "sha": dummy_sha})
        conn.execute(text("INSERT INTO public.evidence_reference VALUES (:inv, :id, :doc)"),
                     {"inv": inv_id, "id": ev_id, "doc": doc_id})
        conn.execute(text("INSERT INTO public.analysis_protocol VALUES (:inv, :id, 'M9-P1-ENV-STATS', '1.0.0', 'Environmental Stats')"),
                     {"inv": inv_id, "id": prot_id})
        conn.execute(text("""
            INSERT INTO public.analytical_result VALUES (
                :inv, :id, :prot, 'deterministic_python_engine', '1.0.0', 'numeric',
                0.2095, 'mol/mol', 'known', NULL,
                :params, :unc, 'FLARE Test Engine', :now
            )
        """), {
            "inv": inv_id, "id": res_id, "prot": prot_id,
            "params": json.dumps({"metric_code": "ambient_initial_o2_median", "canonical_name": "Ambient Initial O2 Median", "sample_size": 129, "quality_flags": []}),
            "unc": json.dumps({"order_statistic_ci": {"lower": "0.2090", "upper": "0.2100"}}),
            "now": now,
        })
        conn.execute(text("""
            INSERT INTO public.aggregate_seal VALUES (
                :inv, :id, :res, 'canonical-json-v2', '{"analytical_result": 1}',
                'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
                'FLARE Test Sealer', :now
            )
        """), {"inv": inv_id, "id": seal_id, "res": res_id, "now": now})
        conn.execute(text("INSERT INTO public.result_evidence VALUES (:inv, :id, :res, :ev, 'primary_source_data')"),
                     {"inv": inv_id, "id": str(uuid4()), "res": res_id, "ev": ev_id})

        # Seed observation data
        conn.execute(text("INSERT INTO public.parse_run VALUES (:inv, :id, :doc)"),
                     {"inv": inv_id, "id": pr_id, "doc": doc_id})
        conn.execute(text("INSERT INTO public.source_record VALUES (:inv, :id, :pr, 2, 'row_2')"),
                     {"inv": inv_id, "id": sr_id, "pr": pr_id})
        conn.execute(text("INSERT INTO public.source_field VALUES (:inv, :id, :pr, 7, 'Initial O2%', '%')"),
                     {"inv": inv_id, "id": sf_id, "pr": pr_id})
        conn.execute(text("INSERT INTO public.experimental_test VALUES (:inv, :id, 'test_01')"),
                     {"inv": inv_id, "id": test_id})
        conn.execute(text("INSERT INTO public.test_source_record VALUES (:inv, :id, :tid, :rid)"),
                     {"inv": inv_id, "id": str(uuid4()), "tid": test_id, "rid": sr_id})
        conn.execute(text("""
            INSERT INTO public.observation VALUES (
                :inv, :id, :pr, :rid, :fid, '20.95', 'numeric', '%', 'observed_variable',
                '{"quality_flags": ["NOMINAL"]}'
            )
        """), {"inv": inv_id, "id": obs_id, "pr": pr_id, "rid": sr_id, "fid": sf_id})

    return engine


# ---------------------------------------------------------------------------
# 1. m9_get_analytical_result Tool Tests
# ---------------------------------------------------------------------------

class TestM9GetAnalyticalResultTool:
    def test_retrieve_valid_metric(self, mock_db_engine):
        with mock_db_engine.connect() as conn:
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
            assert item["unit"] == "mol/mol"
            assert "seal" in item
            assert item["seal"]["seal_version"] == "canonical-json-v2"
            assert len(item["seal"]["member_digest"]) == 64
            assert res.source_hash == AUTHENTIC_BASS_II_SHA256
            assert len(res.evidence_references) >= 1

    def test_rejects_invalid_metric_code(self, mock_db_engine):
        with mock_db_engine.connect() as conn:
            res = execute_m9_get_analytical_result(
                conn=conn,
                parameters={"investigation": "PSI-25", "metric_code": "fake_flame_speed_metric"},
                request_id=uuid4(),
            )
            assert res.execution_status == ToolExecutionStatus.INVALID_INPUT
            assert "Invalid metric_code" in res.limitations[0]

    def test_rejects_invalid_protocol_code(self, mock_db_engine):
        with mock_db_engine.connect() as conn:
            res = execute_m9_get_analytical_result(
                conn=conn,
                parameters={"investigation": "PSI-25", "protocol_code": "M9-P99-UNKNOWN"},
                request_id=uuid4(),
            )
            assert res.execution_status == ToolExecutionStatus.INVALID_INPUT
            assert "Invalid protocol_code" in res.limitations[0]

    def test_empty_results_returns_no_results(self, mock_db_engine):
        with mock_db_engine.connect() as conn:
            res = execute_m9_get_analytical_result(
                conn=conn,
                parameters={"investigation": "PSI-25", "metric_code": "calibrated_airflow_velocity_median"},
                request_id=uuid4(),
            )
            assert res.execution_status == ToolExecutionStatus.NO_RESULTS
            assert res.result_data == []

    def test_unsealed_result_triggers_integrity_failure(self):
        # Create an engine with an unsealed analytical result
        eng = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

        @event.listens_for(eng, "connect")
        def attach_public(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("ATTACH DATABASE ':memory:' AS public")
            cursor.close()

        with eng.begin() as conn:
            conn.execute(text("CREATE TABLE public.investigation (id TEXT, investigation_code TEXT)"))
            conn.execute(text("CREATE TABLE public.analysis_protocol (investigation_id TEXT, id TEXT, protocol_code TEXT, protocol_version TEXT, description TEXT)"))
            conn.execute(text("""
                CREATE TABLE public.analytical_result (
                    investigation_id TEXT, id TEXT, protocol_id TEXT, method TEXT, method_version TEXT,
                    result_kind TEXT, numeric_value REAL, unit TEXT, unit_status TEXT, text_value TEXT,
                    parameters TEXT, uncertainty TEXT, producer_ref TEXT, created_at TIMESTAMP
                )
            """))
            conn.execute(text("CREATE TABLE public.aggregate_seal (investigation_id TEXT, id TEXT, result_id TEXT, seal_version TEXT, member_counts TEXT, member_digest TEXT, sealed_by TEXT, created_at TIMESTAMP)"))
            conn.execute(text("CREATE TABLE public.result_evidence (investigation_id TEXT, id TEXT, result_id TEXT, evidence_id TEXT, role TEXT)"))
            conn.execute(text("CREATE TABLE public.evidence_reference (investigation_id TEXT, id TEXT, source_document_id TEXT)"))
            conn.execute(text("CREATE TABLE public.source_document (investigation_id TEXT, id TEXT, sha256 TEXT, original_filename TEXT)"))

            conn.execute(text("INSERT INTO public.investigation VALUES ('inv1', 'PSI-25')"))
            conn.execute(text("INSERT INTO public.analysis_protocol VALUES ('inv1', 'p1', 'M9-P1-ENV-STATS', '1.0.0', 'desc')"))
            conn.execute(text("""
                INSERT INTO public.analytical_result VALUES (
                    'inv1', 'r1', 'p1', 'm', '1', 'numeric', 0.21, 'mol/mol', 'known', NULL,
                    '{"metric_code": "ambient_initial_o2_median"}', '{}', 'actor', '2026-11-14T00:00:00'
                )
            """))
            # Note: No public.aggregate_seal inserted!

        with eng.connect() as conn:
            res = execute_m9_get_analytical_result(
                conn=conn,
                parameters={"investigation": "PSI-25", "metric_code": "ambient_initial_o2_median"},
                request_id=uuid4(),
            )
            assert res.execution_status == ToolExecutionStatus.INTEGRITY_FAILURE
            assert "Integrity failure" in res.limitations[0]


# ---------------------------------------------------------------------------
# 2. flare_query_observations Tool Tests
# ---------------------------------------------------------------------------

class TestFlareQueryObservationsTool:
    def test_query_by_test_id(self, mock_db_engine):
        with mock_db_engine.connect() as conn:
            res = execute_flare_query_observations(
                conn=conn,
                parameters={"investigation": "PSI-25", "test_number": "test_01"},
                request_id=uuid4(),
            )
            assert res.execution_status == ToolExecutionStatus.SUCCESS
            assert res.tool_id == "flare_query_observations"
            assert len(res.result_data) >= 1
            obs = res.result_data[0]
            assert obs["test_identifier"] == "test_01"
            assert obs["field_name"] == "Initial O2%"
            assert obs["raw_value"] == "20.95"
            assert obs["attribution"] == "experimental_measurement"

    def test_query_by_variable(self, mock_db_engine):
        with mock_db_engine.connect() as conn:
            res = execute_flare_query_observations(
                conn=conn,
                parameters={"investigation": "PSI-25", "variable": "Initial O2%"},
                request_id=uuid4(),
            )
            assert res.execution_status == ToolExecutionStatus.SUCCESS
            assert len(res.result_data) >= 1
            assert res.result_data[0]["field_name"] == "Initial O2%"

    def test_row_limit_enforcement(self, mock_db_engine):
        with mock_db_engine.connect() as conn:
            res = execute_flare_query_observations(
                conn=conn,
                parameters={"investigation": "PSI-25", "limit": 1},
                request_id=uuid4(),
            )
            assert res.execution_status == ToolExecutionStatus.SUCCESS
            assert len(res.result_data) <= 1
            assert res.execution_metadata["applied_limit"] == 1

    def test_query_empty_results(self, mock_db_engine):
        with mock_db_engine.connect() as conn:
            res = execute_flare_query_observations(
                conn=conn,
                parameters={"investigation": "PSI-25", "test_number": "test_999"},
                request_id=uuid4(),
            )
            assert res.execution_status == ToolExecutionStatus.NO_RESULTS
            assert res.result_data == []

    def test_sql_injection_attempt_is_safely_parameterized(self, mock_db_engine):
        with mock_db_engine.connect() as conn:
            # An injection payload as test_number
            res = execute_flare_query_observations(
                conn=conn,
                parameters={"investigation": "PSI-25", "test_number": "test_01' OR 1=1; --"},
                request_id=uuid4(),
            )
            # Must return cleanly (either NO_RESULTS or matches sanitized string) without SQL syntax error
            assert res.execution_status in (ToolExecutionStatus.NO_RESULTS, ToolExecutionStatus.SUCCESS)


# ---------------------------------------------------------------------------
# 3. flare_check_scientific_prohibition Tool Tests
# ---------------------------------------------------------------------------

class TestFlareCheckScientificProhibitionTool:
    def test_check_prohibited_biot_number(self):
        res = execute_flare_check_scientific_prohibition(
            parameters={"concept": "Calculate the Biot number Bi << 0.1 for PMMA."},
            request_id=uuid4(),
        )
        assert res.execution_status == ToolExecutionStatus.PROHIBITED
        assert res.tool_id == "flare_check_scientific_prohibition"
        assert res.result_data["is_prohibited"] is True
        assert "Biot number calculations" in res.limitations[0]

    def test_check_prohibited_rq_comb(self):
        res = execute_flare_check_scientific_prohibition(
            parameters={"concept": "Compute RQ_comb from CO2 and O2."},
            request_id=uuid4(),
        )
        assert res.execution_status == ToolExecutionStatus.PROHIBITED
        assert res.result_data["is_prohibited"] is True

    def test_check_allowed_concept(self):
        res = execute_flare_check_scientific_prohibition(
            parameters={"concept": "What is the median initial oxygen concentration in BASS-II?"},
            request_id=uuid4(),
        )
        assert res.execution_status == ToolExecutionStatus.SUCCESS
        assert res.result_data["is_prohibited"] is False

    def test_check_missing_concept_returns_invalid_input(self):
        res = execute_flare_check_scientific_prohibition(
            parameters={},
            request_id=uuid4(),
        )
        assert res.execution_status == ToolExecutionStatus.INVALID_INPUT


# ---------------------------------------------------------------------------
# 4. flare_retrieve_documents Tool Tests
# ---------------------------------------------------------------------------

class TestFlareRetrieveDocumentsTool:
    def test_document_retrieval_returns_not_implemented(self):
        res = execute_flare_retrieve_documents(
            parameters={"query": "BASS-II technical reports on flame extinction"},
            request_id=uuid4(),
        )
        assert res.execution_status in (ToolExecutionStatus.NOT_IMPLEMENTED, ToolExecutionStatus.NO_RESULTS)
        assert res.tool_id == "flare_retrieve_documents"


# ---------------------------------------------------------------------------
# 5. ToolDispatcher Tests
# ---------------------------------------------------------------------------

class TestToolDispatcher:
    def test_dispatch_allowed_plan(self, mock_db_engine):
        plan = create_execution_plan("What was the median ambient initial O2 concentration in BASS-II?")
        dispatcher = ToolDispatcher(engine=mock_db_engine)
        resp = dispatcher.dispatch_plan(plan)

        assert isinstance(resp, ExecutionResponse)
        assert resp.overall_status == ToolExecutionStatus.SUCCESS
        assert len(resp.tool_results) == 1
        assert resp.tool_results[0].tool_id == "m9_get_analytical_result"

    def test_dispatch_abstained_plan_does_not_execute_tools(self, mock_db_engine):
        plan = create_execution_plan("Calculate the Biot number Bi << 0.1 for thin PMMA.")
        assert plan.state == QueryState.ABSTAINED

        dispatcher = ToolDispatcher(engine=mock_db_engine)
        resp = dispatcher.dispatch_plan(plan)

        assert resp.overall_status == ToolExecutionStatus.PROHIBITED
        assert resp.tool_results == []

    def test_dispatch_rejects_unauthorized_tool(self, mock_db_engine):
        # Construct an artificial plan with an illegal tool
        plan = ExecutionPlan(
            request_id=uuid4(),
            original_question="test question",
            normalized_question="test question",
            intent=IntentEnum.SCIENTIFIC_ANALYSIS,
            investigation="PSI-25",
            requested_metrics=[],
            required_tools=["execute_arbitrary_shell_command"],
            scope_status=ScopeStatusEnum.ALLOWED,
            state=QueryState.READY_FOR_EXECUTION,
        )
        dispatcher = ToolDispatcher(engine=mock_db_engine)
        resp = dispatcher.dispatch_plan(plan)

        assert resp.overall_status == ToolExecutionStatus.INVALID_INPUT
        assert "not an allowlisted tool" in resp.tool_results[0].limitations[0]

    def test_dispatch_deadline_exceeded(self, mock_db_engine):
        plan = create_execution_plan("What was the median ambient initial O2 concentration in BASS-II?")
        # Set an impossibly small deadline (-1 second) to force deadline expiration
        dispatcher = ToolDispatcher(engine=mock_db_engine, request_timeout_seconds=-1.0)
        resp = dispatcher.dispatch_plan(plan)

        assert resp.overall_status == ToolExecutionStatus.TIMEOUT
        assert "deadline exceeded" in resp.tool_results[0].limitations[0]


# ---------------------------------------------------------------------------
# 6. API Endpoint Tests (POST /api/v1/intelligence/execute)
# ---------------------------------------------------------------------------

class TestIntelligenceExecuteApi:
    def test_execute_with_question_text(self, client: TestClient):
        response = client.post(
            "/api/v1/intelligence/execute",
            json={"question": "What is the median initial oxygen concentration in BASS-II?"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "overall_status" in data
        assert "tool_results" in data
        assert "plan" in data
        assert data["plan"]["intent"] == "SCIENTIFIC_ANALYSIS"

    def test_execute_with_precomputed_plan(self, client: TestClient):
        # Step 1: Call /plan
        plan_resp = client.post(
            "/api/v1/intelligence/plan",
            json={"question": "What was the calibrated airflow velocity across tests?"},
        )
        assert plan_resp.status_code == 200
        plan = plan_resp.json()["plan"]

        # Step 2: Call /execute with the plan
        exec_resp = client.post(
            "/api/v1/intelligence/execute",
            json={"plan": plan},
        )
        assert exec_resp.status_code == 200
        data = exec_resp.json()
        assert data["plan"]["intent"] == "SCIENTIFIC_ANALYSIS"
        assert "m9_get_analytical_result" in data["plan"]["required_tools"]

    def test_execute_prohibited_query_returns_prohibited_status(self, client: TestClient):
        response = client.post(
            "/api/v1/intelligence/execute",
            json={"question": "Compute the combustion respiratory quotient RQ_comb from CO2 and O2."},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["overall_status"] == "PROHIBITED"
        assert data["plan"]["state"] == "ABSTAINED"
        assert data["tool_results"] == []

    def test_execute_empty_payload_returns_422(self, client: TestClient):
        response = client.post(
            "/api/v1/intelligence/execute",
            json={},
        )
        assert response.status_code == 422
        assert "Either 'plan' or 'question' must be provided" in response.json()["detail"]

    def test_execute_empty_question_returns_422(self, client: TestClient):
        response = client.post(
            "/api/v1/intelligence/execute",
            json={"question": ""},
        )
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# 7. M10.3.2 Remediation Verification Tests (SEC-01, SEC-02, SEC-04, SEC-05)
# ---------------------------------------------------------------------------

class TestM1032Remediations:
    def test_sec01_client_supplied_forged_plan_is_reconstructed_and_rejected(self, client: TestClient):
        """SEC-01: An external client crafts a forged ExecutionPlan claiming an allowed state for a prohibited inquiry."""
        forged_plan = {
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
        response = client.post(
            "/api/v1/intelligence/execute",
            json={"plan": forged_plan},
        )
        assert response.status_code == 200
        data = response.json()
        # Must be intercepted by server-side reconstruction
        assert data["overall_status"] == "PROHIBITED"
        assert data["plan"]["state"] == "ABSTAINED"
        assert data["plan"]["scope_status"] == "PROHIBITED"
        assert data["tool_results"] == []

    def test_sec04_forged_metric_codes_in_target_metrics_rejected(self, mock_db_engine):
        """SEC-04: Target metrics with forged or unknown metric codes must return INVALID_INPUT, not fall through."""
        with mock_db_engine.connect() as conn:
            res = execute_m9_get_analytical_result(
                conn=conn,
                parameters={"investigation": "PSI-25"},
                request_id=uuid4(),
                target_metrics=["forged_metric_code_1", "forged_metric_code_2"],
            )
            assert res.execution_status == ToolExecutionStatus.INVALID_INPUT
            assert "Invalid target metric codes" in res.limitations[0]

    def test_sec02_tampered_snapshot_digest_triggers_integrity_failure(self):
        """SEC-02: Mismatched snapshot digest triggers INTEGRITY_FAILURE in tool execution."""
        eng = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

        @event.listens_for(eng, "connect")
        def attach_public(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("ATTACH DATABASE ':memory:' AS public")
            cursor.close()

        with eng.begin() as conn:
            conn.execute(text("CREATE TABLE public.investigation (id TEXT, investigation_code TEXT)"))
            conn.execute(text("CREATE TABLE public.analysis_protocol (investigation_id TEXT, id TEXT, protocol_code TEXT, protocol_version TEXT, description TEXT)"))
            conn.execute(text("""
                CREATE TABLE public.analytical_result (
                    investigation_id TEXT, id TEXT, protocol_id TEXT, method TEXT, method_version TEXT,
                    result_kind TEXT, numeric_value REAL, unit TEXT, unit_status TEXT, text_value TEXT,
                    parameters TEXT, uncertainty TEXT, producer_ref TEXT, created_at TIMESTAMP
                )
            """))
            conn.execute(text("CREATE TABLE public.aggregate_seal (investigation_id TEXT, id TEXT, result_id TEXT, seal_version TEXT, member_counts TEXT, member_digest TEXT, sealed_by TEXT, created_at TIMESTAMP)"))
            conn.execute(text("CREATE TABLE public.aggregate_seal_snapshot (result_id TEXT, member_digest TEXT)"))
            conn.execute(text("CREATE TABLE public.result_evidence (investigation_id TEXT, id TEXT, result_id TEXT, evidence_id TEXT, role TEXT)"))
            conn.execute(text("CREATE TABLE public.evidence_reference (investigation_id TEXT, id TEXT, source_document_id TEXT)"))
            conn.execute(text("CREATE TABLE public.source_document (investigation_id TEXT, id TEXT, sha256 TEXT, original_filename TEXT)"))

            conn.execute(text("INSERT INTO public.investigation VALUES ('inv1', 'PSI-25')"))
            conn.execute(text("INSERT INTO public.analysis_protocol VALUES ('inv1', 'p1', 'M9-P1-ENV-STATS', '1.0.0', 'desc')"))
            conn.execute(text("""
                INSERT INTO public.analytical_result VALUES (
                    'inv1', 'r1', 'p1', 'm', '1', 'numeric', 999.99, 'mol/mol', 'known', NULL,
                    '{"metric_code": "ambient_initial_o2_median"}', '{}', 'actor', '2026-11-14T00:00:00'
                )
            """))
            # The seal has the original digest
            conn.execute(text("""
                INSERT INTO public.aggregate_seal VALUES (
                    'inv1', 's1', 'r1', 'canonical-json-v2', '{"analytical_result": 1}',
                    'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
                    'actor', '2026-11-14T00:00:00'
                )
            """))
            # The snapshot recomputes a different digest for 999.99
            conn.execute(text("""
                INSERT INTO public.aggregate_seal_snapshot VALUES (
                    'r1', 'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb'
                )
            """))

        with eng.connect() as conn:
            res = execute_m9_get_analytical_result(
                conn=conn,
                parameters={"investigation": "PSI-25", "metric_code": "ambient_initial_o2_median"},
                request_id=uuid4(),
            )
            assert res.execution_status == ToolExecutionStatus.INTEGRITY_FAILURE
            assert "differs from sealed digest" in res.limitations[0]

    def test_sec05_dynamic_epistemic_attribution(self, mock_db_engine):
        """SEC-05: Epistemic attribution must resolve dynamically and never default unknown classes to experimental."""
        eng = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

        @event.listens_for(eng, "connect")
        def attach_public(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("ATTACH DATABASE ':memory:' AS public")
            cursor.close()

        with eng.begin() as conn:
            conn.execute(text("CREATE TABLE public.investigation (id TEXT, investigation_code TEXT)"))
            conn.execute(text("CREATE TABLE public.source_document (investigation_id TEXT, id TEXT, sha256 TEXT, original_filename TEXT)"))
            conn.execute(text("CREATE TABLE public.parse_run (investigation_id TEXT, id TEXT, source_document_id TEXT)"))
            conn.execute(text("CREATE TABLE public.source_record (investigation_id TEXT, id TEXT, parse_run_id TEXT, source_record_number INTEGER, source_row_id TEXT)"))
            conn.execute(text("CREATE TABLE public.source_field (investigation_id TEXT, id TEXT, parse_run_id TEXT, ordinal INTEGER, original_header TEXT, raw_unit TEXT)"))
            conn.execute(text("CREATE TABLE public.observation (investigation_id TEXT, id TEXT, parse_run_id TEXT, source_record_id TEXT, source_field_id TEXT, raw_value TEXT, source_value_kind TEXT, raw_unit TEXT, parser_classification TEXT, parser_flags TEXT)"))
            conn.execute(text("CREATE TABLE public.experimental_test (investigation_id TEXT, id TEXT, test_identifier TEXT)"))
            conn.execute(text("CREATE TABLE public.test_source_record (investigation_id TEXT, id TEXT, experimental_test_id TEXT, source_record_id TEXT)"))
            conn.execute(text("CREATE TABLE public.semantic_annotation (investigation_id TEXT, id TEXT, observation_id TEXT, variable_id TEXT, numeric_value REAL, interpreted_unit TEXT)"))
            conn.execute(text("CREATE TABLE public.scientific_variable (investigation_id TEXT, id TEXT, variable_code TEXT)"))

            inv_id = "inv_dyn"
            doc_id = "doc_dyn"
            pr_id = "pr_dyn"
            sr_id = "sr_dyn"
            sf_id = "sf_dyn"
            test_id = "test_dyn"

            conn.execute(text("INSERT INTO public.investigation VALUES (:inv, 'PSI-25')"), {"inv": inv_id})
            conn.execute(text("INSERT INTO public.source_document VALUES (:inv, :doc, '1111222233334444555566667777888811112222333344445555666677778888', 'dynamic_source.csv')"), {"inv": inv_id, "doc": doc_id})
            conn.execute(text("INSERT INTO public.parse_run VALUES (:inv, :pr, :doc)"), {"inv": inv_id, "pr": pr_id, "doc": doc_id})
            conn.execute(text("INSERT INTO public.source_record VALUES (:inv, :sr, :pr, 1, 'r1')"), {"inv": inv_id, "sr": sr_id, "pr": pr_id})
            conn.execute(text("INSERT INTO public.source_field VALUES (:inv, :sf, :pr, 1, 'header1', 'mm/s')"), {"inv": inv_id, "sf": sf_id, "pr": pr_id})
            conn.execute(text("INSERT INTO public.experimental_test VALUES (:inv, :t, 'test_01')"), {"inv": inv_id, "t": test_id})
            conn.execute(text("INSERT INTO public.test_source_record VALUES (:inv, 'tsr1', :t, :sr)"), {"inv": inv_id, "t": test_id, "sr": sr_id})

            # Record 1: simulation
            conn.execute(text("""
                INSERT INTO public.observation VALUES (
                    :inv, 'obs1', :pr, :sr, :sf, '10.5', 'numeric', 'mm/s', 'numerical_simulation_flame', '{}'
                )
            """), {"inv": inv_id, "pr": pr_id, "sr": sr_id, "sf": sf_id})

            # Record 2: derived
            conn.execute(text("""
                INSERT INTO public.observation VALUES (
                    :inv, 'obs2', :pr, :sr, :sf, '20.0', 'numeric', 'mm/s', 'derived_quantity_flame', '{}'
                )
            """), {"inv": inv_id, "pr": pr_id, "sr": sr_id, "sf": sf_id})

            # Record 3: unclassified unknown
            conn.execute(text("""
                INSERT INTO public.observation VALUES (
                    :inv, 'obs3', :pr, :sr, :sf, '30.0', 'text', 'mm/s', 'unclassified_speculative', '{}'
                )
            """), {"inv": inv_id, "pr": pr_id, "sr": sr_id, "sf": sf_id})

        with eng.connect() as conn:
            res = execute_flare_query_observations(
                conn=conn,
                parameters={"investigation": "PSI-25"},
                request_id=uuid4(),
            )
            assert res.execution_status == ToolExecutionStatus.SUCCESS
            assert len(res.result_data) == 3
            attributions = [o["attribution"] for o in res.result_data]
            assert attributions[0] == "numerical_simulation"
            assert attributions[1] == "derived_quantity"
            assert attributions[2] == "UNRESOLVED"
            # Verify dynamic source hash
            assert res.source_hash == "1111222233334444555566667777888811112222333344445555666677778888"
