"""Typed schemas for FLARE Milestone 10.3 Scientific Tool Execution Layer.

Defines structured responses, execution statuses, and request models for:
- m9_get_analytical_result
- flare_query_observations
- flare_check_scientific_prohibition
- flare_retrieve_documents (NOT_IMPLEMENTED in M10.3)
"""
from __future__ import annotations

from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from app.intelligence.schemas import ExecutionPlan, PlanRequest
from app.intelligence.synthesis.schemas import SynthesizedResponse


class ToolExecutionStatus(str, Enum):
    """Authoritative execution status taxonomy for FLARE intelligence tools."""
    SUCCESS = "SUCCESS"
    NO_RESULTS = "NO_RESULTS"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"
    PROHIBITED = "PROHIBITED"
    INVALID_INPUT = "INVALID_INPUT"
    TIMEOUT = "TIMEOUT"
    INTEGRITY_FAILURE = "INTEGRITY_FAILURE"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class ToolResult(BaseModel):
    """Standardized, immutable output returned by any FLARE intelligence tool."""
    tool_id: str = Field(..., description="Allowlisted identifier of the tool executed")
    execution_status: ToolExecutionStatus = Field(..., description="Standardized execution outcome status")
    request_id: UUID = Field(..., description="Correlation UUID for this execution turn")
    result_data: dict[str, Any] | list[Any] | None = Field(
        default=None,
        description="Structured analytical metrics, observations, or check results",
    )
    evidence_references: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Traceable references to source documents, records, or reviews",
    )
    source_hash: str | None = Field(
        default=None,
        description="Cryptographic SHA-256 hash of the authoritative source dataset",
    )
    quality_flags: list[str] = Field(
        default_factory=list,
        description="Dataset quality notices, sensor drift flags, or condition flags",
    )
    limitations: list[str] = Field(
        default_factory=list,
        description="Epistemic or experimental limitations governing this result",
    )
    execution_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Execution metrics (duration, statement timeouts, row counts, etc.)",
    )


class ExecutionRequest(BaseModel):
    """Request payload for POST /api/v1/intelligence/execute."""
    plan: ExecutionPlan | None = Field(
        default=None,
        description="Pre-computed execution plan from POST /plan. If omitted, question is required.",
    )
    question: str | None = Field(
        default=None,
        description="Natural language query string. Used to build plan if plan is omitted.",
    )
    investigation: str = Field(
        default="PSI-25",
        description="Target investigation identifier (default: PSI-25 / BASS-II)",
    )
    request_id: UUID | None = Field(
        default=None,
        description="Optional correlation UUID",
    )
    synthesize: bool = Field(
        default=True,
        description="Whether to run grounded scientific synthesis via LLM Layer (M10.5)",
    )


class ExecutionResponse(BaseModel):
    """Response payload returned by POST /api/v1/intelligence/execute."""
    request_id: UUID = Field(..., description="Correlation UUID for this execution")
    plan: ExecutionPlan = Field(..., description="Execution plan governing tool dispatch")
    tool_results: list[ToolResult] = Field(
        default_factory=list,
        description="Ordered results produced by dispatched allowlisted tools",
    )
    overall_status: ToolExecutionStatus = Field(
        ...,
        description="Aggregate execution status across all dispatched tools",
    )
    duration_ms: float = Field(..., description="Total execution wall-clock time in milliseconds")
    synthesis: SynthesizedResponse | None = Field(
        default=None,
        description="Evidence-grounded scientific synthesis (M10.5)",
    )
