"""Typed schemas for FLARE LLM Scientific Intelligence Synthesis (M10.5)."""
from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from app.intelligence.validation.schemas import (
    EpistemicStatus,
    ScientificClaim,
    StableEvidenceReference,
)


class SynthesizedResponse(BaseModel):
    """Structured, evidence-grounded scientific response synthesized for the user."""
    synthesis_id: UUID = Field(default_factory=uuid4)
    answer: str = Field(..., description="Evidence-grounded scientific synthesis in Markdown format")
    key_findings: list[str] = Field(default_factory=list, description="Bulleted summary of verified findings")
    scientific_claims: list[ScientificClaim] = Field(
        default_factory=list,
        description="Strictly validated structured scientific claims (only VALIDATED claims present)",
    )
    evidence_references: list[StableEvidenceReference] = Field(
        default_factory=list,
        description="Traceable references to empirical data or literature chunks",
    )
    uncertainty_and_limitations: list[str] = Field(
        default_factory=list,
        description="Methodological, experimental, or model limitations",
    )
    tools_used: list[str] = Field(
        default_factory=list,
        description="List of allowlisted tool IDs whose outputs grounded this synthesis",
    )
    epistemic_status: EpistemicStatus = Field(
        default=EpistemicStatus.SUPPORTED,
        description="Overall epistemic confidence status",
    )
    provider_status: str = Field(
        default="available",
        description="Status of the synthesis provider: 'available', 'unavailable', 'degraded', 'mock'",
    )
    provider_model: str | None = Field(
        default=None,
        description="Identifier of the LLM model that generated the synthesis",
    )
    rejected_claims_count: int = Field(
        default=0,
        description="Number of draft claims rejected by deterministic validation",
    )
    execution_duration_ms: float = Field(
        default=0.0,
        description="Time taken to produce and validate the synthesis in milliseconds",
    )
