"""Comprehensive test suite for FLARE Milestone 10.2 Intelligence Engine.

Covers:
1. Query Normalization and boundary conditions
2. Deterministic Intent Classification across all 7 supported intents
3. Scientific Scope Gate and Security Boundary Enforcement
4. Typed Execution State Machine and transition graph rules
5. Allowlisted Tool Registry and validation
6. Execution Planner integration
7. API Endpoint (POST /api/v1/intelligence/plan)
"""
from __future__ import annotations

from uuid import UUID, uuid4
import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.intelligence.classifier import classify_intent
from app.intelligence.normalizer import (
    MAX_QUERY_LENGTH,
    MIN_QUERY_LENGTH,
    NormalizedQuery,
    normalize_query,
)
from app.intelligence.planner import create_execution_plan, extract_target_metrics
from app.intelligence.schemas import (
    ExecutionPlan,
    IntentEnum,
    InvalidStateTransitionError,
    InvalidToolError,
    PlanRequest,
    PlanResponse,
    QueryNormalizationError,
    QueryState,
    ScopeStatusEnum,
)
from app.intelligence.scope_gate import evaluate_scope
from app.intelligence.state_machine import ExecutionStateMachine, VALID_TRANSITIONS
from app.intelligence.tools import (
    ALLOWLISTED_TOOLS,
    TOOL_REGISTRY,
    get_tool_definition,
    is_valid_tool,
    validate_tools,
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


# ---------------------------------------------------------------------------
# 1. Query Normalization Tests
# ---------------------------------------------------------------------------

class TestQueryNormalizer:
    def test_normalizer_strips_and_collapses_whitespace(self):
        raw = "   What   is   the   median   \t\n  initial   oxygen   concentration?   \n"
        norm = normalize_query(raw)
        assert isinstance(norm, NormalizedQuery)
        assert norm.original == raw
        assert norm.normalized == "What is the median initial oxygen concentration?"

    def test_normalizer_rejects_empty_string(self):
        with pytest.raises(QueryNormalizationError, match="empty or whitespace-only"):
            normalize_query("")

    def test_normalizer_rejects_whitespace_only(self):
        with pytest.raises(QueryNormalizationError, match="empty or whitespace-only"):
            normalize_query("   \t  \n \r  ")

    def test_normalizer_rejects_too_short(self):
        with pytest.raises(QueryNormalizationError, match="too short"):
            normalize_query("ab")

    def test_normalizer_accepts_minimum_length(self):
        norm = normalize_query("O2?")
        assert len(norm.normalized) == 3
        assert norm.normalized == "O2?"

    def test_normalizer_rejects_too_long(self):
        oversized = "a" * (MAX_QUERY_LENGTH + 1)
        with pytest.raises(QueryNormalizationError, match="exceeds maximum length"):
            normalize_query(oversized)

    def test_normalizer_rejects_non_string(self):
        with pytest.raises(QueryNormalizationError, match="must be a string"):
            normalize_query(12345)  # type: ignore


# ---------------------------------------------------------------------------
# 2. Intent Classification Tests
# ---------------------------------------------------------------------------

class TestIntentClassifier:
    def test_classify_scientific_analysis(self):
        q = "What is the median initial oxygen concentration in BASS-II?"
        assert classify_intent(q) == IntentEnum.SCIENTIFIC_ANALYSIS

    def test_classify_scientific_analysis_airflow(self):
        q = "What is the calibrated airflow velocity IQR for BASS-II burns?"
        assert classify_intent(q) == IntentEnum.SCIENTIFIC_ANALYSIS

    def test_classify_observation_lookup(self):
        q = "What were the raw observation values recorded in test_04?"
        assert classify_intent(q) == IntentEnum.OBSERVATION_LOOKUP

    def test_classify_document_retrieval(self):
        q = "Can you provide the NASA technical report and README documentation for BASS-II?"
        assert classify_intent(q) == IntentEnum.DOCUMENT_RETRIEVAL

    def test_classify_combined_research(self):
        q = "What papers discuss the median oxygen depletion measured during flight runs?"
        assert classify_intent(q) == IntentEnum.COMBINED_RESEARCH

    def test_classify_scientific_explanation(self):
        q = "Why does radiation loss cause quiescent flame extinction in microgravity?"
        assert classify_intent(q) == IntentEnum.SCIENTIFIC_EXPLANATION

    def test_classify_out_of_scope(self):
        q = "What is the weather forecast for tomorrow in New York?"
        assert classify_intent(q) == IntentEnum.OUT_OF_SCOPE

    def test_classify_ambiguous(self):
        q = "tell me more"
        assert classify_intent(q) == IntentEnum.AMBIGUOUS


# ---------------------------------------------------------------------------
# 3. Scientific Scope Gate & Security Tests
# ---------------------------------------------------------------------------

class TestScopeGate:
    def test_scope_gate_allows_valid_combustion_query(self):
        status, reason = evaluate_scope("What is the median initial ambient oxygen in BASS-II?")
        assert status == ScopeStatusEnum.ALLOWED
        assert reason is None

    # Prohibited scientific inquiries
    def test_prohibits_biot_number(self):
        status, reason = evaluate_scope("Can you calculate the Biot number Bi << 0.1 for thin PMMA?")
        assert status == ScopeStatusEnum.PROHIBITED
        assert "Biot number calculations" in reason

    def test_prohibits_rq_comb(self):
        status, reason = evaluate_scope("Calculate the combustion respiratory quotient RQ_comb from CO2 and O2.")
        assert status == ScopeStatusEnum.PROHIBITED
        assert "RQ_comb" in reason

    def test_prohibits_slab_loi_regression(self):
        status, reason = evaluate_scope("Run logistic regression to calculate thick slab LOI extinction.")
        assert status == ScopeStatusEnum.PROHIBITED
        assert "Thick slab Limiting Oxygen Index (LOI) logistic regression is prohibited" in reason

    def test_prohibits_flame_spread_rate(self):
        status, reason = evaluate_scope("What is the flame spread rate V_f for test 23?")
        assert status == ScopeStatusEnum.PROHIBITED
        assert "Flame spread rate (V_f) calculations are not supported" in reason

    def test_prohibits_molar_consumption(self):
        status, reason = evaluate_scope("Calculate the total molar consumption delta n_O2 of oxygen.")
        assert status == ScopeStatusEnum.PROHIBITED
        assert "Absolute molar consumption (delta n_O2) cannot be derived" in reason

    def test_prohibits_cubic_flow_polynomial(self):
        status, reason = evaluate_scope("Compute the cubic flow polynomial calibration curve.")
        assert status == ScopeStatusEnum.PROHIBITED
        assert "Cubic flow polynomials are prohibited" in reason

    def test_prohibits_lunar_martian_extrapolation(self):
        status, reason = evaluate_scope("Extrapolate these flame spread results to lunar gravity conditions.")
        assert status == ScopeStatusEnum.PROHIBITED
        assert "lunar gravity" in reason or "Lunar 1/6 g" in reason

    def test_prohibits_fire_risk_odds_ratios(self):
        status, reason = evaluate_scope("What is the fire risk odds ratio for PMMA vs Nomex?")
        assert status == ScopeStatusEnum.PROHIBITED
        assert "Fire-risk odds ratios are prohibited" in reason

    # Security Invariant tests (SQL Injection)
    def test_prohibits_sql_injection_select(self):
        status, reason = evaluate_scope("SELECT * FROM observation_record WHERE 1=1")
        assert status == ScopeStatusEnum.PROHIBITED
        assert "SQL injection" in reason

    def test_prohibits_sql_injection_union(self):
        status, reason = evaluate_scope("test_01 UNION SELECT username, password FROM users")
        assert status == ScopeStatusEnum.PROHIBITED
        assert "SQL injection" in reason

    def test_prohibits_sql_injection_drop_table(self):
        status, reason = evaluate_scope("test_01; DROP TABLE analysis_protocol; --")
        assert status == ScopeStatusEnum.PROHIBITED
        assert "SQL injection" in reason

    def test_prohibits_sql_injection_tautology(self):
        status, reason = evaluate_scope("test_01 OR 1=1")
        assert status == ScopeStatusEnum.PROHIBITED
        assert "SQL injection" in reason

    # Security Invariant tests (Code Injection)
    def test_prohibits_code_injection_eval(self):
        status, reason = evaluate_scope("Can you run eval('1+1') on the telemetry?")
        assert status == ScopeStatusEnum.PROHIBITED
        assert "arbitrary code execution" in reason

    def test_prohibits_code_injection_import_os(self):
        status, reason = evaluate_scope("import os; os.system('dir')")
        assert status == ScopeStatusEnum.PROHIBITED
        assert "arbitrary code execution" in reason

    # Out-of-scope and Ambiguity tests
    def test_detects_out_of_scope_cooking(self):
        status, reason = evaluate_scope("How to bake a chocolate cake?")
        assert status == ScopeStatusEnum.OUT_OF_SCOPE
        assert "outside the scope of FLARE" in reason

    def test_detects_out_of_scope_stocks(self):
        status, reason = evaluate_scope("What is the stock price of Apple?")
        assert status == ScopeStatusEnum.OUT_OF_SCOPE

    def test_detects_ambiguous_short_query(self):
        status, reason = evaluate_scope("what happened?")
        assert status == ScopeStatusEnum.AMBIGUOUS
        assert "too ambiguous" in reason or "too brief" in reason


# ---------------------------------------------------------------------------
# 4. State Machine Tests
# ---------------------------------------------------------------------------

class TestStateMachine:
    def test_valid_lifecycle_progression(self):
        sm = ExecutionStateMachine(QueryState.RECEIVED)
        assert sm.current_state == QueryState.RECEIVED

        sm.transition_to(QueryState.NORMALIZED, "Input cleaned")
        assert sm.current_state == QueryState.NORMALIZED

        sm.transition_to(QueryState.CLASSIFIED, "Intent detected")
        assert sm.current_state == QueryState.CLASSIFIED

        sm.transition_to(QueryState.SCOPE_VALIDATED, "Scope checked")
        assert sm.current_state == QueryState.SCOPE_VALIDATED

        sm.transition_to(QueryState.PLANNED, "Plan generated")
        assert sm.current_state == QueryState.PLANNED

        sm.transition_to(QueryState.READY_FOR_EXECUTION, "Tools confirmed")
        assert sm.current_state == QueryState.READY_FOR_EXECUTION

        assert len(sm.history) == 5

    def test_valid_abstention_progression(self):
        sm = ExecutionStateMachine(QueryState.RECEIVED)
        sm.transition_to(QueryState.NORMALIZED)
        sm.transition_to(QueryState.CLASSIFIED)
        sm.transition_to(QueryState.SCOPE_VALIDATED)
        sm.transition_to(QueryState.ABSTAINED, "Prohibited inquiry")
        assert sm.current_state == QueryState.ABSTAINED

    def test_illegal_transition_raises_error(self):
        sm = ExecutionStateMachine(QueryState.RECEIVED)
        with pytest.raises(InvalidStateTransitionError, match="Illegal state transition"):
            sm.transition_to(QueryState.PLANNED)  # Cannot skip NORMALIZED, CLASSIFIED, SCOPE_VALIDATED

    def test_cannot_transition_from_terminal_abstained(self):
        sm = ExecutionStateMachine(QueryState.RECEIVED)
        sm.transition_to(QueryState.NORMALIZED)
        sm.transition_to(QueryState.CLASSIFIED)
        sm.transition_to(QueryState.SCOPE_VALIDATED)
        sm.transition_to(QueryState.ABSTAINED)

        with pytest.raises(InvalidStateTransitionError, match="Illegal state transition"):
            sm.transition_to(QueryState.PLANNED)

    def test_cannot_transition_from_terminal_failed(self):
        sm = ExecutionStateMachine(QueryState.RECEIVED)
        sm.fail("Fatal syntax error")
        assert sm.current_state == QueryState.FAILED

        with pytest.raises(InvalidStateTransitionError, match="Illegal state transition"):
            sm.transition_to(QueryState.NORMALIZED)


# ---------------------------------------------------------------------------
# 5. Tool Registry & Allowlist Tests
# ---------------------------------------------------------------------------

class TestToolRegistry:
    def test_allowlisted_tools_present(self):
        expected = {
            "m9_get_analytical_result",
            "flare_query_observations",
            "flare_retrieve_documents",
            "flare_check_scientific_prohibition",
        }
        assert set(ALLOWLISTED_TOOLS) == expected

    def test_is_valid_tool(self):
        assert is_valid_tool("m9_get_analytical_result") is True
        assert is_valid_tool("execute_arbitrary_sql") is False

    def test_validate_tools_success(self):
        validate_tools(["m9_get_analytical_result", "flare_retrieve_documents"])

    def test_validate_tools_failure(self):
        with pytest.raises(InvalidToolError, match="not an allowlisted tool"):
            validate_tools(["m9_get_analytical_result", "unauthorized_tool"])

    def test_get_tool_definition(self):
        defn = get_tool_definition("m9_get_analytical_result")
        assert defn.name == "m9_get_analytical_result"
        assert "sealed M9 scientific analytical results" in defn.description
        assert "properties" in defn.parameters_schema


# ---------------------------------------------------------------------------
# 6. Execution Planner Tests
# ---------------------------------------------------------------------------

class TestExecutionPlanner:
    def test_plan_scientific_analysis_ambient_oxygen(self):
        plan = create_execution_plan("What was the median ambient initial O2 concentration in BASS-II?")
        assert plan.state == QueryState.READY_FOR_EXECUTION
        assert plan.scope_status == ScopeStatusEnum.ALLOWED
        assert plan.intent == IntentEnum.SCIENTIFIC_ANALYSIS
        assert "m9_get_analytical_result" in plan.required_tools
        assert "ambient_initial_o2_median" in plan.requested_metrics
        assert "ambient_initial_o2_iqr" in plan.requested_metrics
        assert plan.requires_document_retrieval is False
        assert plan.abstention_reason is None

    def test_plan_scientific_analysis_airflow(self):
        plan = create_execution_plan("What was the calibrated airflow velocity across tests?")
        assert plan.state == QueryState.READY_FOR_EXECUTION
        assert plan.scope_status == ScopeStatusEnum.ALLOWED
        assert "calibrated_airflow_velocity_median" in plan.requested_metrics
        assert "calibrated_airflow_velocity_iqr" in plan.requested_metrics
        assert "calibrated_airflow_velocity_range" in plan.requested_metrics

    def test_plan_scientific_analysis_oxygen_depletion(self):
        plan = create_execution_plan("What was the relative oxygen depletion ratio across BASS-II tests?")
        assert plan.state == QueryState.READY_FOR_EXECUTION
        assert "relative_o2_depletion_ratio_median" in plan.requested_metrics

    def test_plan_observation_lookup(self):
        plan = create_execution_plan("Show me the raw observation values for test_08.")
        assert plan.state == QueryState.READY_FOR_EXECUTION
        assert plan.intent == IntentEnum.OBSERVATION_LOOKUP
        assert plan.required_tools == ["flare_query_observations"]

    def test_plan_document_retrieval(self):
        plan = create_execution_plan("Retrieve the README and protocol documents for BASS-II.")
        assert plan.state == QueryState.READY_FOR_EXECUTION
        assert plan.intent == IntentEnum.DOCUMENT_RETRIEVAL
        assert plan.required_tools == ["flare_retrieve_documents"]
        assert plan.requires_document_retrieval is True

    def test_plan_combined_research(self):
        plan = create_execution_plan("What technical papers discuss the median airflow velocity measured during tests?")
        assert plan.state == QueryState.READY_FOR_EXECUTION
        assert plan.intent == IntentEnum.COMBINED_RESEARCH
        assert "m9_get_analytical_result" in plan.required_tools
        assert "flare_retrieve_documents" in plan.required_tools
        assert plan.requires_document_retrieval is True

    def test_plan_prohibited_query_abstains(self):
        plan = create_execution_plan("Calculate the Biot number Bi << 0.1 for the PMMA slab.")
        assert plan.state == QueryState.ABSTAINED
        assert plan.scope_status == ScopeStatusEnum.PROHIBITED
        assert "Biot number calculations" in plan.abstention_reason
        assert plan.required_tools == []
        assert plan.requested_metrics == []

    def test_plan_out_of_scope_query_abstains(self):
        plan = create_execution_plan("What is the weather forecast for tomorrow?")
        assert plan.state == QueryState.ABSTAINED
        assert plan.scope_status == ScopeStatusEnum.OUT_OF_SCOPE
        assert plan.required_tools == []

    def test_plan_ambiguous_query_abstains(self):
        plan = create_execution_plan("tell me more")
        assert plan.state == QueryState.ABSTAINED
        assert plan.scope_status == ScopeStatusEnum.AMBIGUOUS
        assert plan.required_tools == []


# ---------------------------------------------------------------------------
# 7. API Endpoint Tests (POST /api/v1/intelligence/plan)
# ---------------------------------------------------------------------------

class TestIntelligencePlanApi:
    def test_post_plan_success(self, client: TestClient):
        response = client.post(
            "/api/v1/intelligence/plan",
            json={"question": "What is the median initial oxygen concentration in BASS-II?"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "plan" in data
        plan = data["plan"]
        assert plan["state"] == "READY_FOR_EXECUTION"
        assert plan["scope_status"] == "ALLOWED"
        assert plan["intent"] == "SCIENTIFIC_ANALYSIS"
        assert "m9_get_analytical_result" in plan["required_tools"]
        assert "ambient_initial_o2_median" in plan["requested_metrics"]

    def test_post_plan_prohibited_returns_abstained(self, client: TestClient):
        response = client.post(
            "/api/v1/intelligence/plan",
            json={"question": "Run logistic regression to calculate thick slab LOI extinction."},
        )
        assert response.status_code == 200
        data = response.json()
        plan = data["plan"]
        assert plan["state"] == "ABSTAINED"
        assert plan["scope_status"] == "PROHIBITED"
        assert "Thick slab Limiting Oxygen Index (LOI) logistic regression is prohibited" in plan["abstention_reason"]
        assert plan["required_tools"] == []

    def test_post_plan_sql_injection_prohibited(self, client: TestClient):
        response = client.post(
            "/api/v1/intelligence/plan",
            json={"question": "test_01; DROP TABLE analysis_protocol; --"},
        )
        assert response.status_code == 200
        data = response.json()
        plan = data["plan"]
        assert plan["state"] == "ABSTAINED"
        assert plan["scope_status"] == "PROHIBITED"
        assert "SQL injection" in plan["abstention_reason"]

    def test_post_plan_empty_question_returns_422(self, client: TestClient):
        response = client.post(
            "/api/v1/intelligence/plan",
            json={"question": ""},
        )
        assert response.status_code == 422

    def test_post_plan_whitespace_only_returns_422(self, client: TestClient):
        response = client.post(
            "/api/v1/intelligence/plan",
            json={"question": "     \n\t   "},
        )
        assert response.status_code == 422

    def test_post_plan_too_short_returns_422(self, client: TestClient):
        response = client.post(
            "/api/v1/intelligence/plan",
            json={"question": "hi"},
        )
        assert response.status_code == 422
        assert "too short" in response.json()["detail"]

    def test_post_plan_preserves_custom_request_id(self, client: TestClient):
        req_id = str(uuid4())
        response = client.post(
            "/api/v1/intelligence/plan",
            json={
                "question": "What was the calibrated airflow velocity across tests?",
                "investigation": "PSI-25",
                "request_id": req_id,
            },
        )
        assert response.status_code == 200
        plan = response.json()["plan"]
        assert plan["request_id"] == req_id
        assert plan["investigation"] == "PSI-25"
