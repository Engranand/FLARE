"""Execution Planner for FLARE Milestone 10.2 Intelligence Engine.

Deterministic query understanding, scope verification, and plan assembly:
- Coordinates normalizer, classifier, scope gate, and state machine
- Maps natural-language requests to authoritative M9 metric codes
- Determines required allowlisted tools and execution dependencies
- Yields immutable, typed ExecutionPlan objects
"""
from __future__ import annotations

import re
from typing import Sequence
from uuid import UUID, uuid4

from app.intelligence.classifier import classify_intent
from app.intelligence.normalizer import normalize_query
from app.intelligence.schemas import (
    ExecutionPlan,
    IntentEnum,
    QueryNormalizationError,
    QueryState,
    ScopeStatusEnum,
)
from app.intelligence.scope_gate import evaluate_scope
from app.intelligence.state_machine import ExecutionStateMachine
from app.intelligence.tools import validate_tools

# Authoritative set of 20 M9 metric codes
M9_METRIC_CODES: list[str] = [
    "ambient_initial_o2_median",
    "ambient_initial_o2_iqr",
    "ambient_initial_co2_median",
    "ambient_initial_co2_iqr",
    "ambient_initial_co_median",
    "ambient_initial_co_iqr",
    "non_negative_o2_depletion_median",
    "non_negative_o2_depletion_iqr",
    "relative_o2_depletion_ratio_median",
    "positive_o2_depletion_median",
    "positive_o2_depletion_iqr",
    "signed_distribution_o2_depletion_median",
    "calibrated_airflow_velocity_median",
    "calibrated_airflow_velocity_iqr",
    "calibrated_airflow_velocity_range",
    "total_flight_runs_count",
    "unique_physical_specimens_count",
    "first_burn_subset_runs_count",
    "subsequent_reburn_subset_runs_count",
    "observed_morphology_regimes_summary",
]


def extract_target_metrics(normalized_question: str) -> list[str]:
    """Identify requested M9 metric codes from question content.
    
    Args:
        normalized_question: Sanitized query string.
        
    Returns:
        List of matching M9 metric codes in deterministic order.
    """
    matched: list[str] = []
    q = normalized_question.lower()

    # Environmental gas metrics (P1)
    if re.search(r"\b(ambient|initial)\s+o2\b|\boxygen\s+concentration\b", q):
        matched.extend(["ambient_initial_o2_median", "ambient_initial_o2_iqr"])
    if re.search(r"\b(ambient|initial)\s+co2\b|\bcarbon\s+dioxide\b", q):
        matched.extend(["ambient_initial_co2_median", "ambient_initial_co2_iqr"])
    if re.search(r"\b(ambient|initial)\s+co\b|\bcarbon\s+monoxide\b", q):
        matched.extend(["ambient_initial_co_median", "ambient_initial_co_iqr"])

    # Oxygen depletion metrics (P2)
    if "relative" in q and "depletion" in q:
        matched.append("relative_o2_depletion_ratio_median")
    elif "positive" in q and "depletion" in q:
        matched.extend(["positive_o2_depletion_median", "positive_o2_depletion_iqr"])
    elif "signed" in q and "depletion" in q:
        matched.append("signed_distribution_o2_depletion_median")
    elif re.search(r"\b(o2\s+depletion|oxygen\s+depletion|depleted|consumed\s+o2)\b", q):
        matched.extend(["non_negative_o2_depletion_median", "non_negative_o2_depletion_iqr"])

    # Airflow velocity metrics (P3)
    if re.search(r"\b(airflow|air\s+flow|flow\s+velocity|duct\s+velocity|air\s+speed)\b", q):
        matched.extend([
            "calibrated_airflow_velocity_median",
            "calibrated_airflow_velocity_iqr",
            "calibrated_airflow_velocity_range",
        ])

    # Fuel morphology and specimen counts (P4)
    if re.search(r"\b(how\s+many\s+tests|flight\s+runs|total\s+runs|total\s+tests)\b", q):
        matched.append("total_flight_runs_count")
    if re.search(r"\b(specimen\s+count|unique\s+specimens|how\s+many\s+samples)\b", q):
        matched.append("unique_physical_specimens_count")
    if re.search(r"\b(first\s+burn|virgin\s+burn)\b", q):
        matched.append("first_burn_subset_runs_count")
    if re.search(r"\b(reburn|subsequent\s+burn)\b", q):
        matched.append("subsequent_reburn_subset_runs_count")
    if re.search(r"\b(morphology|regime|pmma\s+flat|pmma\s+rod|cotton|nomex)\b", q):
        matched.append("observed_morphology_regimes_summary")

    # If general metrics or statistics requested without specific metric keywords
    if not matched and re.search(r"\b(statistic|summary|m9\s+metric|analysis\s+result|metric)\b", q):
        matched.extend([
            "ambient_initial_o2_median",
            "non_negative_o2_depletion_median",
            "calibrated_airflow_velocity_median",
            "total_flight_runs_count",
        ])

    # Deduplicate while preserving order
    seen: set[str] = set()
    result: list[str] = []
    for m in matched:
        if m not in seen and m in M9_METRIC_CODES:
            seen.add(m)
            result.append(m)

    return result


def create_execution_plan(
    question: str,
    investigation: str = "PSI-25",
    request_id: UUID | None = None,
) -> ExecutionPlan:
    """Create a deterministic execution plan for an incoming user question.
    
    Args:
        question: User query string.
        investigation: Target investigation identifier.
        request_id: Optional caller tracking UUID.
        
    Returns:
        ExecutionPlan detailing intent, scope, tools, metrics, and state.
    """
    plan_id = request_id or uuid4()
    sm = ExecutionStateMachine(initial_state=QueryState.RECEIVED)

    # 1. Normalize query
    norm_result = normalize_query(question)
    sm.transition_to(QueryState.NORMALIZED, reason="Query sanitized and collapsed")

    # 2. Classify intent
    intent = classify_intent(norm_result.normalized)
    sm.transition_to(QueryState.CLASSIFIED, reason=f"Intent classified as {intent.value}")

    # 3. Evaluate scope
    scope_status, abstention_reason = evaluate_scope(norm_result.normalized)
    sm.transition_to(QueryState.SCOPE_VALIDATED, reason=f"Scope status determined as {scope_status.value}")

    # 4. Handle non-allowed scopes (Abstain early)
    if scope_status != ScopeStatusEnum.ALLOWED:
        sm.transition_to(QueryState.ABSTAINED, reason=abstention_reason)
        return ExecutionPlan(
            request_id=plan_id,
            original_question=norm_result.original,
            normalized_question=norm_result.normalized,
            intent=intent,
            investigation=investigation,
            requested_metrics=[],
            required_tools=[],
            requires_document_retrieval=False,
            scope_status=scope_status,
            abstention_reason=abstention_reason,
            execution_dependencies=[],
            state=QueryState.ABSTAINED,
            error_message=None,
        )

    # 5. Planning permitted: determine tools and metrics
    sm.transition_to(QueryState.PLANNED, reason="Query within scope, assembling execution components")

    requested_metrics = extract_target_metrics(norm_result.normalized)

    required_tools: list[str] = []
    dependencies: list[str] = []
    requires_doc_retrieval = False

    if intent == IntentEnum.SCIENTIFIC_ANALYSIS:
        required_tools = ["m9_get_analytical_result"]
        dependencies = ["step_1:fetch_m9_metrics"]
    elif intent == IntentEnum.OBSERVATION_LOOKUP:
        required_tools = ["flare_query_observations"]
        dependencies = ["step_1:query_telemetry_observations"]
    elif intent == IntentEnum.DOCUMENT_RETRIEVAL:
        required_tools = ["flare_retrieve_documents"]
        dependencies = ["step_1:retrieve_literature_passages"]
        requires_doc_retrieval = True
    elif intent == IntentEnum.COMBINED_RESEARCH:
        required_tools = ["m9_get_analytical_result", "flare_retrieve_documents"]
        dependencies = [
            "step_1:fetch_m9_metrics",
            "step_2:retrieve_literature_passages",
            "step_3:synthesize_empirical_and_contextual_evidence",
        ]
        requires_doc_retrieval = True
    elif intent == IntentEnum.SCIENTIFIC_EXPLANATION:
        required_tools = ["flare_retrieve_documents"]
        dependencies = ["step_1:retrieve_theoretical_and_protocol_context"]
        requires_doc_retrieval = True

    # Validate tools against allowlist
    validate_tools(required_tools)

    # 6. Ready for Execution
    sm.transition_to(QueryState.READY_FOR_EXECUTION, reason="Execution plan assembled and tools validated")

    return ExecutionPlan(
        request_id=plan_id,
        original_question=norm_result.original,
        normalized_question=norm_result.normalized,
        intent=intent,
        investigation=investigation,
        requested_metrics=requested_metrics,
        required_tools=required_tools,
        requires_document_retrieval=requires_doc_retrieval,
        scope_status=scope_status,
        abstention_reason=None,
        execution_dependencies=dependencies,
        state=QueryState.READY_FOR_EXECUTION,
        error_message=None,
    )
