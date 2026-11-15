"""Typed Pydantic schemas and enums for FLARE Milestone 10.2 Intelligence Engine.

Governed by FLARE Milestone 10 Architecture and Security Contracts:
- Intent classification without false LLM semantic claims
- Strict scope gating with scientific prohibition checks
- Typed execution state machine states
- Execution plan and API request/response structures
"""
from __future__ import annotations

from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class IntentEnum(str, Enum):
    """Explicitly supported question intents."""
    SCIENTIFIC_ANALYSIS = "SCIENTIFIC_ANALYSIS"
    OBSERVATION_LOOKUP = "OBSERVATION_LOOKUP"
    DOCUMENT_RETRIEVAL = "DOCUMENT_RETRIEVAL"
    COMBINED_RESEARCH = "COMBINED_RESEARCH"
    SCIENTIFIC_EXPLANATION = "SCIENTIFIC_EXPLANATION"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"
    AMBIGUOUS = "AMBIGUOUS"


class ScopeStatusEnum(str, Enum):
    """Scientific and operational scope gating statuses."""
    ALLOWED = "ALLOWED"
    PROHIBITED = "PROHIBITED"
    AMBIGUOUS = "AMBIGUOUS"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"


class QueryState(str, Enum):
    """Lifecycle states of the execution state machine."""
    RECEIVED = "RECEIVED"
    NORMALIZED = "NORMALIZED"
    CLASSIFIED = "CLASSIFIED"
    SCOPE_VALIDATED = "SCOPE_VALIDATED"
    PLANNED = "PLANNED"
    READY_FOR_EXECUTION = "READY_FOR_EXECUTION"
    ABSTAINED = "ABSTAINED"
    FAILED = "FAILED"


class ExecutionPlan(BaseModel):
    """Deterministic execution plan produced by the M10.2 orchestration layer."""
    request_id: UUID = Field(default_factory=uuid4, description="Unique plan request tracking UUID")
    original_question: str = Field(..., description="Original raw question submitted by user")
    normalized_question: str = Field(..., description="Sanitized and normalized question string")
    intent: IntentEnum = Field(..., description="Classified intent category")
    investigation: str = Field(default="PSI-25", description="Target investigation (default: PSI-25 / BASS-II)")
    requested_metrics: list[str] = Field(default_factory=list, description="Target M9 metric codes identified in query")
    required_tools: list[str] = Field(default_factory=list, description="Allowlisted tools required for execution")
    requires_document_retrieval: bool = Field(default=False, description="Whether contextual document retrieval is needed")
    scope_status: ScopeStatusEnum = Field(..., description="Scope gate assessment outcome")
    abstention_reason: str | None = Field(default=None, description="Explicit rationale when scope is not ALLOWED")
    execution_dependencies: list[str] = Field(default_factory=list, description="Ordered dependency step identifiers")
    state: QueryState = Field(..., description="Terminal state of the state machine after planning")
    error_message: str | None = Field(default=None, description="Error details if state is FAILED")


class PlanRequest(BaseModel):
    """Incoming request to POST /api/v1/intelligence/plan."""
    question: str = Field(..., min_length=1, description="Natural language question to plan execution for")
    investigation: str = Field(default="PSI-25", description="Target scientific investigation (e.g. PSI-25 / BASS-II)")
    request_id: UUID | None = Field(default=None, description="Optional caller-supplied request tracking UUID")


class PlanResponse(BaseModel):
    """Response returned by POST /api/v1/intelligence/plan."""
    plan: ExecutionPlan = Field(..., description="Generated deterministic execution plan")


class QueryNormalizationError(ValueError):
    """Raised when an incoming query cannot be sanitized or normalized."""
    pass


class InvalidStateTransitionError(RuntimeError):
    """Raised when an illegal state machine transition is attempted."""
    pass


class InvalidToolError(ValueError):
    """Raised when a non-allowlisted tool is requested or validated."""
    pass


class ScientificProhibitionError(ValueError):
    """Raised when a query violates explicit scientific or safety prohibitions."""
    pass
