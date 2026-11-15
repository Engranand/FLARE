"""FLARE M10.5 Runtime Verification Suite: Live Scenarios 1-4.

Executes runtime verification against real PostgreSQL 17 and live Ollama daemon:
- Scenario 1: Live Ollama query execution and structured synthesis schema conformance.
- Scenario 2: Scientific claim validation (valid, wrong value, wrong unit, wrong sample size, narrative invariant).
- Scenario 3: Deterministic fallback when Ollama is unavailable (provider_status='unavailable').
- Scenario 4: Evidence traceability (resolving to M9 results/chunks, rejecting unsupported references).
"""
from __future__ import annotations

from decimal import Decimal
import json
from pathlib import Path
from uuid import UUID

import pytest
import httpx
from fastapi.testclient import TestClient

from app.analysis.engine import ROOT_DIR
from app.intelligence.llm.ollama import OllamaProvider
from app.intelligence.llm.mock import MockLLMProvider
from app.intelligence.synthesis.synthesizer import ScientificSynthesisService
from app.intelligence.validation.claim_validator import ClaimValidator
from app.intelligence.validation.schemas import (
    ClaimType,
    ClaimValidationStatus,
    EpistemicStatus,
    EvidenceType,
    ScientificClaim,
    StableEvidenceReference,
)
from app.main import create_app
from tests.integration.test_m10_5_integration import m10_5_db

pytestmark = pytest.mark.postgres


def test_scenario_1_live_ollama_runtime_query(m10_5_db):
    """Scenario 1: Live Ollama reachability, model check, and end-to-end query synthesis."""
    # 1. Verify Ollama is reachable and qwen2.5:3b is available
    provider = OllamaProvider(base_url="http://127.0.0.1:11434", model="qwen2.5:3b")
    assert provider.is_available(), "Ollama daemon at http://127.0.0.1:11434 must be running and healthy"

    # 2. Configure FLARE app with live Ollama provider
    app = create_app()
    app.state.db_engine = m10_5_db
    app.state.synthesis_service = ScientificSynthesisService(provider=provider)

    client = TestClient(app)
    query = "What was the median ambient initial oxygen concentration in BASS-II?"
    response = client.post(
        "/api/v1/intelligence/execute",
        json={
            "question": query,
            "investigation": "PSI-25",
            "synthesize": True,
        },
    )

    assert response.status_code == 200, f"API returned error: {response.text}"
    data = response.json()
    assert data["overall_status"] == "SUCCESS"
    assert "synthesis" in data
    synth = data["synthesis"]
    assert synth is not None, "Expected synthesis object in response"

    # 3. Verify structured synthesis schema conformance
    assert isinstance(synth["synthesis_id"], str) and len(synth["synthesis_id"]) > 0
    # Must be valid UUID format
    UUID(synth["synthesis_id"])

    assert synth["provider_status"] == "available", f"Expected 'available', got '{synth['provider_status']}'"
    assert synth["provider_model"] == "qwen2.5:3b"

    assert isinstance(synth["answer"], str) and len(synth["answer"].strip()) > 20
    assert isinstance(synth["key_findings"], list)
    assert isinstance(synth["scientific_claims"], list)
    assert isinstance(synth["evidence_references"], list)
    assert isinstance(synth["uncertainty_and_limitations"], list)
    assert isinstance(synth["tools_used"], list)
    assert "m9_get_analytical_result" in synth["tools_used"]

    assert synth["epistemic_status"] in ["SUPPORTED", "UNRESOLVED", "HYPOTHESIS", "DISPUTED"]
    assert isinstance(synth["rejected_claims_count"], int)
    assert synth["rejected_claims_count"] >= 0
    assert isinstance(synth["execution_duration_ms"], (int, float))
    assert synth["execution_duration_ms"] > 0

    print("\n--- LIVE OLLAMA SYNTHESIS RESULT ---")
    print("Provider Status:", synth["provider_status"], f"({synth['provider_model']})")
    print("Latency:", f"{synth['execution_duration_ms']:.1f}ms")
    print("Epistemic Status:", synth["epistemic_status"])
    print("Answer:\n", synth["answer"])
    print("Key Findings:", synth["key_findings"])
    print("Claims Validated Count:", len(synth["scientific_claims"]))
    print("Claims Rejected Count:", synth["rejected_claims_count"])
    print("Uncertainty & Limitations:\n", json.dumps(synth["uncertainty_and_limitations"], indent=2))
    print("------------------------------------\n")


def test_scenario_2_scientific_claim_validation(m10_5_db):
    """Scenario 2: Scientific claim validation under nominal and adversarial conditions."""
    # Build sealed M9 results dictionary matching BASS-II P1 determination
    sealed_m9 = {
        "ambient_initial_o2_median": {
            "metric_code": "ambient_initial_o2_median",
            "protocol_code": "M9-P1-ENV-STATS",
            "numeric_value": 0.182,
            "unit": "mol/mol",
            "sample_size": 129,
            "ci_lower": 0.175,
            "ci_upper": 0.188,
        }
    }
    validator = ClaimValidator(sealed_m9_results=sealed_m9)

    # 2a. Test Valid Claim
    valid_claim = ScientificClaim(
        claim_type=ClaimType.STATISTICAL_METRIC,
        subject_entity="ambient_initial_o2",
        claimed_statement="Median initial oxygen mole fraction was 0.182 mol/mol (N=129).",
        metric_identifier="ambient_initial_o2_median",
        claimed_numeric_value=Decimal("0.182"),
        claimed_unit="mol/mol",
        claimed_sample_size=129,
        evidence_references=[
            StableEvidenceReference(
                uri="flare:result:M9-P1-ENV-STATS:ambient_initial_o2_median",
                evidence_type=EvidenceType.DERIVED_QUANTITY,
                epistemic_status=EpistemicStatus.SUPPORTED,
                location_label="BASS-II Environmental Gas Statistics",
                summary_snippet="Median initial oxygen",
            )
        ],
    )
    res_valid = validator.validate_claim(valid_claim)
    assert res_valid.validation_status == ClaimValidationStatus.VALIDATED
    assert res_valid.validation_error is None
    assert res_valid.epistemic_verdict == EpistemicStatus.SUPPORTED

    # 2b. Test Intentionally Incorrect Numerical Value (0.450 instead of 0.182)
    wrong_val_claim = ScientificClaim(
        claim_type=ClaimType.STATISTICAL_METRIC,
        subject_entity="ambient_initial_o2",
        claimed_statement="Median initial oxygen mole fraction was 0.450 mol/mol.",
        metric_identifier="ambient_initial_o2_median",
        claimed_numeric_value=Decimal("0.450"),
        claimed_unit="mol/mol",
        claimed_sample_size=129,
        evidence_references=[
            StableEvidenceReference(
                uri="flare:result:M9-P1-ENV-STATS:ambient_initial_o2_median",
                evidence_type=EvidenceType.DERIVED_QUANTITY,
                epistemic_status=EpistemicStatus.SUPPORTED,
                location_label="BASS-II Environmental Gas Statistics",
                summary_snippet="Median initial oxygen",
            )
        ],
    )
    res_wrong_val = validator.validate_claim(wrong_val_claim)
    assert res_wrong_val.validation_status == ClaimValidationStatus.REJECTED
    assert "Numeric value mismatch" in (res_wrong_val.validation_error or "")
    assert res_wrong_val.epistemic_verdict == EpistemicStatus.DISPUTED

    # 2c. Test Incorrect Unit ("kPa" instead of "mol/mol")
    wrong_unit_claim = ScientificClaim(
        claim_type=ClaimType.STATISTICAL_METRIC,
        subject_entity="ambient_initial_o2",
        claimed_statement="Median initial oxygen was 0.182 kPa.",
        metric_identifier="ambient_initial_o2_median",
        claimed_numeric_value=Decimal("0.182"),
        claimed_unit="kPa",
        claimed_sample_size=129,
        evidence_references=[
            StableEvidenceReference(
                uri="flare:result:M9-P1-ENV-STATS:ambient_initial_o2_median",
                evidence_type=EvidenceType.DERIVED_QUANTITY,
                epistemic_status=EpistemicStatus.SUPPORTED,
                location_label="BASS-II Environmental Gas Statistics",
                summary_snippet="Median initial oxygen",
            )
        ],
    )
    res_wrong_unit = validator.validate_claim(wrong_unit_claim)
    assert res_wrong_unit.validation_status == ClaimValidationStatus.REJECTED
    assert "Unit mismatch" in (res_wrong_unit.validation_error or "")
    assert res_wrong_unit.epistemic_verdict == EpistemicStatus.DISPUTED

    # 2d. Test Incorrect Sample Size (N=999 instead of 129)
    wrong_n_claim = ScientificClaim(
        claim_type=ClaimType.STATISTICAL_METRIC,
        subject_entity="ambient_initial_o2",
        claimed_statement="Median initial oxygen mole fraction was 0.182 mol/mol across 999 tests.",
        metric_identifier="ambient_initial_o2_median",
        claimed_numeric_value=Decimal("0.182"),
        claimed_unit="mol/mol",
        claimed_sample_size=999,
        evidence_references=[
            StableEvidenceReference(
                uri="flare:result:M9-P1-ENV-STATS:ambient_initial_o2_median",
                evidence_type=EvidenceType.DERIVED_QUANTITY,
                epistemic_status=EpistemicStatus.SUPPORTED,
                location_label="BASS-II Environmental Gas Statistics",
                summary_snippet="Median initial oxygen",
            )
        ],
    )
    res_wrong_n = validator.validate_claim(wrong_n_claim)
    assert res_wrong_n.validation_status == ClaimValidationStatus.REJECTED
    assert "Sample size mismatch" in (res_wrong_n.validation_error or "")
    assert res_wrong_n.epistemic_verdict == EpistemicStatus.DISPUTED

    # 2e. Narrative Invariant: rejected claims NEVER appear as validated quantitative findings
    canned_with_bad_claim = {
        "answer": "BASS-II recorded an initial oxygen fraction of 0.450 mol/mol.",
        "key_findings": [
            "Oxygen fraction was 0.450 mol/mol.",
            "Valid general observation.",
        ],
        "scientific_claims": [
            {
                "claim_type": "STATISTICAL_METRIC",
                "subject_entity": "ambient_initial_o2",
                "claimed_statement": "Oxygen fraction was 0.450 mol/mol.",
                "metric_identifier": "ambient_initial_o2_median",
                "claimed_numeric_value": 0.450,
                "claimed_unit": "mol/mol",
                "claimed_sample_size": 129,
                "evidence_references": [
                    {
                        "uri": "flare:result:M9-P1-ENV-STATS:ambient_initial_o2_median",
                        "evidence_type": "DQ",
                        "epistemic_status": "SUPPORTED",
                        "location_label": "BASS-II Stats",
                        "summary_snippet": "Oxygen reading",
                    }
                ],
            }
        ],
        "epistemic_status": "SUPPORTED",
    }
    mock_prov = MockLLMProvider(default_response=canned_with_bad_claim)
    app = create_app()
    app.state.db_engine = m10_5_db
    app.state.synthesis_service = ScientificSynthesisService(provider=mock_prov)
    client = TestClient(app)

    res = client.post(
        "/api/v1/intelligence/execute",
        json={"question": "What was the median ambient initial oxygen concentration in BASS-II?"},
    )
    assert res.status_code == 200
    synth = res.json()["synthesis"]
    assert synth["rejected_claims_count"] == 1
    # Check that the hallucinated 0.450 claim is rejected and purged from validated claims
    assert len(synth["scientific_claims"]) == 0
    assert any("Numeric value mismatch" in lim for lim in synth["uncertainty_and_limitations"])
    assert "excluded from verified findings" in synth["answer"]
    # Check that key_findings does NOT contain the rejected claim text
    for finding in synth["key_findings"]:
        assert "0.450" not in finding, "Narrative invariant violation: rejected numeric claim leaked into findings"


def test_scenario_3_deterministic_fallback(m10_5_db):
    """Scenario 3: Deterministic fallback when Ollama daemon is unreachable."""
    # Point provider to unreachable port to simulate offline daemon
    offline_provider = OllamaProvider(base_url="http://127.0.0.1:54321", model="qwen2.5:3b")
    assert not offline_provider.is_available(), "Offline provider must report unavailable"

    app = create_app()
    app.state.db_engine = m10_5_db
    app.state.synthesis_service = ScientificSynthesisService(provider=offline_provider)

    client = TestClient(app)
    response = client.post(
        "/api/v1/intelligence/execute",
        json={
            "question": "What was the median ambient initial oxygen concentration in BASS-II?",
            "investigation": "PSI-25",
            "synthesize": True,
        },
    )

    # Must gracefully return HTTP 200, never HTTP 500
    assert response.status_code == 200
    data = response.json()
    assert data["overall_status"] == "SUCCESS"
    synth = data["synthesis"]
    assert synth is not None

    # Verify fallback state
    assert synth["provider_status"] == "unavailable"
    assert len(synth["answer"].strip()) > 0
    # Confirm deterministic answer contains the sealed M9 value
    assert "0.182" in synth["answer"]
    assert "mol/mol" in synth["answer"]

    # Confirm limitations include the fallback notice
    lims = synth["uncertainty_and_limitations"]
    assert any("unavailable" in lim.lower() for lim in lims)

    # Confirm verified claims were built deterministically from M9
    assert len(synth["scientific_claims"]) >= 1
    assert synth["scientific_claims"][0]["validation_status"] == "VALIDATED"
    assert synth["scientific_claims"][0]["metric_identifier"] == "ambient_initial_o2_median"


def test_scenario_4_evidence_traceability(m10_5_db):
    """Scenario 4: Evidence traceability and rejection of unsupported references."""
    sealed_m9 = {
        "ambient_initial_o2_median": {
            "metric_code": "ambient_initial_o2_median",
            "protocol_code": "M9-P1-ENV-STATS",
            "numeric_value": 0.182,
            "unit": "mol/mol",
            "sample_size": 129,
        }
    }
    validator = ClaimValidator(sealed_m9_results=sealed_m9)

    # 4a. Valid Evidence Reference with flare: URI
    claim_valid_ref = ScientificClaim(
        claim_type=ClaimType.STATISTICAL_METRIC,
        subject_entity="ambient_initial_o2",
        claimed_statement="Initial oxygen median was 0.182 mol/mol.",
        metric_identifier="ambient_initial_o2_median",
        claimed_numeric_value=Decimal("0.182"),
        claimed_unit="mol/mol",
        evidence_references=[
            StableEvidenceReference(
                uri="flare:result:M9-P1-ENV-STATS:ambient_initial_o2_median",
                evidence_type=EvidenceType.DERIVED_QUANTITY,
                epistemic_status=EpistemicStatus.SUPPORTED,
                location_label="BASS-II Environmental Gas Statistics",
                summary_snippet="Initial O2 median",
            )
        ],
    )
    res_valid_ref = validator.validate_claim(claim_valid_ref)
    assert res_valid_ref.validation_status == ClaimValidationStatus.VALIDATED

    # 4b. Missing / Empty Evidence Reference for Quantitative Claim
    claim_no_ref = ScientificClaim(
        claim_type=ClaimType.STATISTICAL_METRIC,
        subject_entity="ambient_initial_o2",
        claimed_statement="Initial oxygen median was 0.182 mol/mol.",
        metric_identifier="ambient_initial_o2_median",
        claimed_numeric_value=Decimal("0.182"),
        claimed_unit="mol/mol",
        evidence_references=[],  # Empty
    )
    res_no_ref = validator.validate_claim(claim_no_ref)
    assert res_no_ref.validation_status == ClaimValidationStatus.REJECTED
    assert "at least one evidence reference" in (res_no_ref.validation_error or "").lower()

    # 4c. Non-flare / Unsupported URI Scheme
    claim_bad_scheme = ScientificClaim(
        claim_type=ClaimType.STATISTICAL_METRIC,
        subject_entity="ambient_initial_o2",
        claimed_statement="Initial oxygen median was 0.182 mol/mol.",
        metric_identifier="ambient_initial_o2_median",
        claimed_numeric_value=Decimal("0.182"),
        claimed_unit="mol/mol",
        evidence_references=[
            StableEvidenceReference(
                uri="https://untrusted-external-site.com/fake_o2",
                evidence_type=EvidenceType.REFERENCE_THEORETICAL,
                epistemic_status=EpistemicStatus.UNRESOLVED,
                location_label="Untrusted Link",
                summary_snippet="Fake snippet",
            )
        ],
    )
    res_bad_scheme = validator.validate_claim(claim_bad_scheme)
    assert res_bad_scheme.validation_status == ClaimValidationStatus.REJECTED
    assert "Must start with 'flare:'" in (res_bad_scheme.validation_error or "")

    # 4d. Unresolvable / Non-existent Metric Reference
    claim_nonexistent_metric = ScientificClaim(
        claim_type=ClaimType.STATISTICAL_METRIC,
        subject_entity="fabricated_rate",
        claimed_statement="Fabricated combustion rate is 42.0.",
        metric_identifier="nonexistent_m9_metric_xyz",
        claimed_numeric_value=Decimal("42.0"),
        claimed_unit="cm/s",
        evidence_references=[
            StableEvidenceReference(
                uri="flare:result:M9-P9:nonexistent_m9_metric_xyz",
                evidence_type=EvidenceType.DERIVED_QUANTITY,
                epistemic_status=EpistemicStatus.SUPPORTED,
                location_label="Fake",
                summary_snippet="Fake",
            )
        ],
    )
    res_nonexistent = validator.validate_claim(claim_nonexistent_metric)
    assert res_nonexistent.validation_status == ClaimValidationStatus.REJECTED
    assert "not found in sealed M9" in (res_nonexistent.validation_error or "")
    assert res_nonexistent.epistemic_verdict == EpistemicStatus.UNRESOLVED
