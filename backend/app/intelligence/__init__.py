"""FLARE Scientific Intelligence Module (Milestone 10).

Provides deterministic query understanding, scientific scope gating, state machine orchestration,
allowlisted tool contracts, and the M10.3 Tool Execution Layer.
"""
from app.intelligence.classifier import classify_intent
from app.intelligence.dispatcher import ToolDispatcher
from app.intelligence.normalizer import NormalizedQuery, normalize_query
from app.intelligence.planner import create_execution_plan
from app.intelligence.schemas import (
    ExecutionPlan,
    IntentEnum,
    InvalidStateTransitionError,
    InvalidToolError,
    PlanRequest,
    PlanResponse,
    QueryNormalizationError,
    QueryState,
    ScientificProhibitionError,
    ScopeStatusEnum,
)
from app.intelligence.scope_gate import evaluate_scope
from app.intelligence.state_machine import ExecutionStateMachine
from app.intelligence.tool_executor import (
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
from app.intelligence.tools import (
    ALLOWLISTED_TOOLS,
    TOOL_REGISTRY,
    ToolDefinition,
    get_tool_definition,
    is_valid_tool,
    validate_tools,
)

__all__ = [
    "ALLOWLISTED_TOOLS",
    "ExecutionPlan",
    "ExecutionRequest",
    "ExecutionResponse",
    "ExecutionStateMachine",
    "IntentEnum",
    "InvalidStateTransitionError",
    "InvalidToolError",
    "NormalizedQuery",
    "PlanRequest",
    "PlanResponse",
    "QueryNormalizationError",
    "QueryState",
    "ScientificProhibitionError",
    "ScopeStatusEnum",
    "TOOL_REGISTRY",
    "ToolDefinition",
    "ToolDispatcher",
    "ToolExecutionStatus",
    "ToolResult",
    "classify_intent",
    "create_execution_plan",
    "evaluate_scope",
    "execute_flare_check_scientific_prohibition",
    "execute_flare_query_observations",
    "execute_flare_retrieve_documents",
    "execute_m9_get_analytical_result",
    "get_tool_definition",
    "is_valid_tool",
    "normalize_query",
    "validate_tools",
]
