"""Scientific Claim Validation Layer for FLARE M10.5."""
from app.intelligence.validation.claim_validator import ClaimValidator
from app.intelligence.validation.schemas import (
    ClaimType,
    ClaimValidationStatus,
    EpistemicStatus,
    EvidenceType,
    ScientificClaim,
    StableEvidenceReference,
    ValidatedClaimBundle,
)

__all__ = [
    "ClaimValidator",
    "ClaimType",
    "ClaimValidationStatus",
    "EpistemicStatus",
    "EvidenceType",
    "ScientificClaim",
    "StableEvidenceReference",
    "ValidatedClaimBundle",
]
