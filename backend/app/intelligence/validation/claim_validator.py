"""Deterministic Scientific Claim Validator for FLARE M10.5.

Validates structured claims against sealed M9 analytical results, retrieved literature
chunks, and authoritative M9 scientific prohibitions.
"""
from __future__ import annotations

from decimal import Decimal
import logging
import re
from typing import Any

from app.intelligence.validation.schemas import (
    ClaimType,
    ClaimValidationStatus,
    EpistemicStatus,
    ScientificClaim,
    ValidatedClaimBundle,
)

logger = logging.getLogger(__name__)

# Authoritative M9 scientific prohibitions
PROHIBITED_TERMS = [
    (r"\bbiot\b", "Biot number calculations are strictly prohibited."),
    (r"\bloi\s+regression\b|\blimiting\s+oxygen\s+index\b", "Limiting Oxygen Index (LOI) regression on fuel slabs is prohibited."),
    (r"\blunar\b|\bmartian\b|\bmoon\b|\bmars\b", "Extrapolation to lunar or Martian gravity is prohibited without direct flight data."),
    (r"\bflame\s+spread\s+rate\b|\bflame\s+propagation\s+speed\b", "Uncalibrated flame spread rate prediction is prohibited."),
    (r"\bodds\s+ratio\b|\bfire\s+risk\s+odds\b", "Fire risk odds ratios are prohibited from deterministic flight telemetry."),
]


class ClaimValidator:
    """Validates structured draft claims against sealed ground truth and safety constraints."""

    def __init__(
        self,
        sealed_m9_results: dict[str, dict[str, Any]] | None = None,
        retrieved_documents: list[dict[str, Any]] | None = None,
    ) -> None:
        self.sealed_m9_results = sealed_m9_results or {}
        self.retrieved_documents = retrieved_documents or []
        self._retrieved_hashes = {
            doc.get("source_hash")
            for doc in self.retrieved_documents
            if doc.get("source_hash")
        }

    def validate_claim(self, claim: ScientificClaim) -> ScientificClaim:
        """Validate a single scientific claim object."""
        combined_text = f"{claim.subject_entity} {claim.claimed_statement}".lower()

        # 1. Scientific Prohibitions Check
        for pattern, reason in PROHIBITED_TERMS:
            if re.search(pattern, combined_text, re.IGNORECASE):
                claim.validation_status = ClaimValidationStatus.REJECTED
                claim.validation_error = f"Prohibited scientific concept: {reason}"
                claim.epistemic_verdict = EpistemicStatus.DISPUTED
                return claim

        # 2. Statistical Metric Verification
        if claim.claim_type == ClaimType.STATISTICAL_METRIC or claim.metric_identifier:
            metric_key = claim.metric_identifier
            if metric_key and metric_key not in self.sealed_m9_results and ":" in metric_key:
                # Safely normalize protocol or URI prefix (e.g. "M9-P1-ENV-STATS:ambient_initial_o2_median" -> "ambient_initial_o2_median")
                candidate = metric_key.split(":")[-1]
                if candidate in self.sealed_m9_results:
                    metric_key = candidate
                    claim.metric_identifier = candidate

            if not metric_key or metric_key not in self.sealed_m9_results:
                claim.validation_status = ClaimValidationStatus.REJECTED
                claim.validation_error = (
                    f"Metric identifier '{claim.metric_identifier}' not found in sealed M9 analytical results."
                )
                claim.epistemic_verdict = EpistemicStatus.UNRESOLVED
                return claim

            expected_data = self.sealed_m9_results[metric_key]

            # 2a. Exact Numeric Value Verification
            if claim.claimed_numeric_value is not None:
                expected_raw = expected_data.get("numeric_value")
                if expected_raw is not None:
                    expected_val = Decimal(str(expected_raw))
                    # Allow 0.02 numerical tolerance for float conversions or rounding in narrative
                    if abs(claim.claimed_numeric_value - expected_val) > Decimal("0.02"):
                        claim.validation_status = ClaimValidationStatus.REJECTED
                        claim.validation_error = (
                            f"Numeric value mismatch for {claim.metric_identifier}: "
                            f"claimed {claim.claimed_numeric_value}, expected {expected_val}"
                        )
                        claim.epistemic_verdict = EpistemicStatus.DISPUTED
                        return claim

            # 2b. Unit Verification
            if claim.claimed_unit:
                expected_unit = expected_data.get("unit")
                if expected_unit and claim.claimed_unit.strip().lower() != expected_unit.strip().lower():
                    # Handle equivalent percentage / fraction representation if applicable
                    if not (claim.claimed_unit.strip() in {"%", "fraction"} and expected_unit.strip() == "mol/mol"):
                        claim.validation_status = ClaimValidationStatus.REJECTED
                        claim.validation_error = (
                            f"Unit mismatch for {claim.metric_identifier}: "
                            f"claimed '{claim.claimed_unit}', expected '{expected_unit}'"
                        )
                        claim.epistemic_verdict = EpistemicStatus.DISPUTED
                        return claim

            # 2c. Sample Size Verification
            if claim.claimed_sample_size is not None:
                expected_n = expected_data.get("sample_size")
                if expected_n is not None and claim.claimed_sample_size != expected_n:
                    claim.validation_status = ClaimValidationStatus.REJECTED
                    claim.validation_error = (
                        f"Sample size mismatch for {claim.metric_identifier}: "
                        f"claimed N={claim.claimed_sample_size}, expected N={expected_n}"
                    )
                    claim.epistemic_verdict = EpistemicStatus.DISPUTED
                    return claim

        # 3. Evidence Resolvability Verification
        if not claim.evidence_references:
            # If there are no references at all, qualify or reject depending on claim type
            if claim.claim_type in {ClaimType.STATISTICAL_METRIC, ClaimType.NUMERICAL_MEASUREMENT}:
                claim.validation_status = ClaimValidationStatus.REJECTED
                claim.validation_error = "Quantitative claim must contain at least one evidence reference."
                claim.epistemic_verdict = EpistemicStatus.UNRESOLVED
                return claim
        else:
            for ev in claim.evidence_references:
                if not ev.uri.startswith("flare:"):
                    claim.validation_status = ClaimValidationStatus.REJECTED
                    claim.validation_error = f"Invalid evidence URI format '{ev.uri}'. Must start with 'flare:'"
                    claim.epistemic_verdict = EpistemicStatus.UNRESOLVED
                    return claim

        # Passed all checks
        claim.validation_status = ClaimValidationStatus.VALIDATED
        claim.validation_error = None
        claim.epistemic_verdict = EpistemicStatus.SUPPORTED
        return claim

    def validate_bundle(self, claims: list[ScientificClaim]) -> ValidatedClaimBundle:
        """Validate a list of claims and package them into a bundle."""
        validated_claims: list[ScientificClaim] = []
        rejection_reasons: list[str] = []

        for c in claims:
            v_claim = self.validate_claim(c)
            validated_claims.append(v_claim)
            if v_claim.validation_status == ClaimValidationStatus.REJECTED and v_claim.validation_error:
                rejection_reasons.append(v_claim.validation_error)

        all_validated = all(c.validation_status == ClaimValidationStatus.VALIDATED for c in validated_claims)
        return ValidatedClaimBundle(
            claims=validated_claims,
            all_validated=all_validated,
            rejection_reasons=rejection_reasons,
        )
