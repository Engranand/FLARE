"""Authoritative schemas for Typed Scientific Claims and Evidence Grounding (M10.5)."""
from __future__ import annotations

from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class EvidenceType(str, Enum):
    """Physical origin taxonomy for scientific evidence."""
    EXPERIMENTAL_MEASUREMENT = "EM"  # Flight transducer readouts (photodiodes, O2 sensor cells)
    NUMERICAL_SIMULATION = "NS"      # Differential governing equation integrations (CHEMKIN, CFD)
    DERIVED_QUANTITY = "DQ"          # Deterministic reduction from measurements (medians, IQR, U_inf)
    REFERENCE_THEORETICAL = "RT"     # Calibration gases, equilibrium limits, manufacturer specs

    # Short aliases for contract compatibility
    EM = "EM"
    NS = "NS"
    DQ = "DQ"
    RT = "RT"


class EpistemicStatus(str, Enum):
    """Verification quality and epistemic status of evidence and claims."""
    SUPPORTED = "SUPPORTED"      # Conforms to instrumentation standards and matches sealed M9 truth
    DISPUTED = "DISPUTED"        # Conflicting observations or sensor drift detected
    UNRESOLVED = "UNRESOLVED"    # Incomplete documentation or attribution prevents verification
    HYPOTHESIS = "HYPOTHESIS"    # Theoretical conjecture or unverified physical model


class ClaimType(str, Enum):
    """Semantic classification of scientific claim objects."""
    NUMERICAL_MEASUREMENT = "NUMERICAL_MEASUREMENT"
    STATISTICAL_METRIC = "STATISTICAL_METRIC"
    MATERIAL_CLASSIFICATION = "MATERIAL_CLASSIFICATION"
    EXPERIMENTAL_REGIME = "EXPERIMENTAL_REGIME"
    METHODOLOGICAL_LIMITATION = "METHODOLOGICAL_LIMITATION"


class ClaimValidationStatus(str, Enum):
    """Validation verdict assigned by the deterministic ClaimValidator."""
    PENDING = "PENDING"
    VALIDATED = "VALIDATED"
    REJECTED = "REJECTED"
    QUALIFIED = "QUALIFIED"


class StableEvidenceReference(BaseModel):
    """Stable, resolvable scientific evidence pointer with provenance URN."""
    uri: str = Field(..., description="Stable URN e.g. flare:result:M9-P1-ENV-STATS:ambient_initial_o2_median")
    evidence_type: EvidenceType = Field(default=EvidenceType.EM, description="Physical origin taxonomy")
    epistemic_status: EpistemicStatus = Field(default=EpistemicStatus.SUPPORTED, description="Verification status")
    source_sha256: str | None = Field(default=None, description="SHA-256 hash of authoritative source document")
    location_label: str = Field(default="", description="Human-readable citation label (e.g. Page 7, Table 2)")
    summary_snippet: str = Field(default="", description="Grounded excerpt or metric summary")


class ScientificClaim(BaseModel):
    """Structured Scientific Claim Object formulated during synthesis."""
    claim_id: UUID = Field(default_factory=uuid4)
    claim_type: ClaimType = Field(default=ClaimType.STATISTICAL_METRIC)
    subject_entity: str = Field(..., description="Entity or variable name (e.g. ambient_initial_o2, PMMA slab)")
    claimed_statement: str = Field(..., description="Natural language scientific assertion")
    
    # Exact numeric specification
    claimed_numeric_value: Decimal | None = None
    claimed_unit: str | None = None
    metric_identifier: str | None = None  # e.g. ambient_initial_o2_median
    
    # Uncertainty bounds
    claimed_ci_lower: Decimal | None = None
    claimed_ci_upper: Decimal | None = None
    claimed_sample_size: int | None = None
    
    # Multi-evidence linkage
    evidence_references: list[StableEvidenceReference] = Field(default_factory=list)
    
    # Validation state
    validation_status: ClaimValidationStatus = Field(default=ClaimValidationStatus.PENDING)
    validation_error: str | None = None
    epistemic_verdict: EpistemicStatus = Field(default=EpistemicStatus.SUPPORTED)


class ValidatedClaimBundle(BaseModel):
    """Collection of validated and rejected claims for a query turn."""
    claims: list[ScientificClaim] = Field(default_factory=list)
    all_validated: bool = True
    rejection_reasons: list[str] = Field(default_factory=list)
