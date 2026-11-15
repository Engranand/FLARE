"""Unit tests for FLARE Milestone 10.5 — LLM Scientific Intelligence Integration."""
from __future__ import annotations

from decimal import Decimal
import json
from uuid import uuid4

import pytest
from starlette.testclient import TestClient

from app.intelligence.llm.base import ProviderUnavailableError
from app.intelligence.llm.mock import MockLLMProvider
from app.intelligence.llm.ollama import OllamaProvider
from app.intelligence.planner import create_execution_plan
from app.intelligence.schemas import IntentEnum, QueryState, ScopeStatusEnum
from app.intelligence.synthesis.prompt_builder import build_synthesis_prompt
from app.intelligence.synthesis.schemas import SynthesizedResponse
from app.intelligence.synthesis.synthesizer import ScientificSynthesisService
from app.intelligence.tool_schemas import ExecutionRequest, ToolExecutionStatus, ToolResult
from app.intelligence.validation.claim_validator import ClaimValidator
from app.intelligence.validation.schemas import (
    ClaimType,
    ClaimValidationStatus,
    EpistemicStatus,
    EvidenceType,
    ScientificClaim,
    StableEvidenceReference,
)
from app.main import app


class TestLLMProviders:
    """Test LLM provider abstraction, mock provider, and error handling."""

    def test_mock_provider_canned_response(self):
        canned = {
            "answer": "Grounded synthesis for BASS-II.",
            "key_findings": ["Oxygen depletion observed."],
            "scientific_claims": [],
            "uncertainty_and_limitations": ["Limited sample."],
            "epistemic_status": "SUPPORTED",
        }
        mock_p = MockLLMProvider(default_response=canned)
        assert mock_p.is_available() is True
        assert mock_p.provider_name == "mock"

        res = mock_p.generate_sync("Test prompt")
        assert res.model == "mock-flare-v1"
        data = json.loads(res.content)
        assert data["answer"] == "Grounded synthesis for BASS-II."
        assert mock_p.invocation_count == 1

    def test_mock_provider_offline_raises_unavailable(self):
        mock_p = MockLLMProvider(available=False)
        assert mock_p.is_available() is False
        with pytest.raises(ProviderUnavailableError) as exc_info:
            mock_p.generate_sync("Test prompt")
        assert "Mock provider configured as offline" in str(exc_info.value)

    def test_ollama_provider_unreachable_raises_unavailable(self):
        # Point to unused port to verify graceful ProviderUnavailableError
        ollama_p = OllamaProvider(base_url="http://127.0.0.1:59999", timeout_seconds=1.0)
        assert ollama_p.is_available() is False
        with pytest.raises(ProviderUnavailableError) as exc_info:
            ollama_p.generate_sync("Test prompt")
        assert "Cannot connect to Ollama" in str(exc_info.value) or "Ollama" in str(exc_info.value)


class TestClaimValidator:
    """Test deterministic verification of structured scientific claims."""

    @pytest.fixture
    def sealed_m9_results(self):
        return {
            "ambient_initial_o2_median": {
                "metric_code": "ambient_initial_o2_median",
                "protocol_code": "M9-P1-ENV-STATS",
                "numeric_value": 0.21,
                "unit": "mol/mol",
                "sample_size": 129,
                "ci_lower": 0.20,
                "ci_upper": 0.22,
            },
            "calibrated_airflow_velocity_median": {
                "metric_code": "calibrated_airflow_velocity_median",
                "protocol_code": "M9-P3-AIRFLOW",
                "numeric_value": 2.45,
                "unit": "cm/s",
                "sample_size": 129,
                "ci_lower": 2.10,
                "ci_upper": 2.80,
            },
        }

    @pytest.fixture
    def validator(self, sealed_m9_results):
        return ClaimValidator(sealed_m9_results=sealed_m9_results)

    def test_valid_m9_claim_passes(self, validator):
        claim = ScientificClaim(
            claim_type=ClaimType.STATISTICAL_METRIC,
            subject_entity="ambient_initial_o2",
            claimed_statement="Median initial oxygen mole fraction was 0.21 mol/mol across 129 tests.",
            metric_identifier="ambient_initial_o2_median",
            claimed_numeric_value=Decimal("0.21"),
            claimed_unit="mol/mol",
            claimed_sample_size=129,
            evidence_references=[
                StableEvidenceReference(
                    uri="flare:result:M9-P1-ENV-STATS:ambient_initial_o2_median",
                    evidence_type=EvidenceType.DERIVED_QUANTITY,
                    epistemic_status=EpistemicStatus.SUPPORTED,
                )
            ],
        )
        res = validator.validate_claim(claim)
        assert res.validation_status == ClaimValidationStatus.VALIDATED
        assert res.epistemic_verdict == EpistemicStatus.SUPPORTED
        assert res.validation_error is None

    def test_claim_value_mismatch_rejected(self, validator):
        claim = ScientificClaim(
            claim_type=ClaimType.STATISTICAL_METRIC,
            subject_entity="ambient_initial_o2",
            claimed_statement="Median initial oxygen was 0.35 mol/mol.",
            metric_identifier="ambient_initial_o2_median",
            claimed_numeric_value=Decimal("0.35"),  # Actual is 0.21
            claimed_unit="mol/mol",
            evidence_references=[
                StableEvidenceReference(uri="flare:result:M9-P1-ENV-STATS:ambient_initial_o2_median")
            ],
        )
        res = validator.validate_claim(claim)
        assert res.validation_status == ClaimValidationStatus.REJECTED
        assert "Numeric value mismatch" in str(res.validation_error)
        assert res.epistemic_verdict == EpistemicStatus.DISPUTED

    def test_claim_unit_mismatch_rejected(self, validator):
        claim = ScientificClaim(
            claim_type=ClaimType.STATISTICAL_METRIC,
            subject_entity="calibrated_airflow_velocity",
            claimed_statement="Median airflow velocity was 2.45 m/s.",
            metric_identifier="calibrated_airflow_velocity_median",
            claimed_numeric_value=Decimal("2.45"),
            claimed_unit="m/s",  # Actual is cm/s
            evidence_references=[
                StableEvidenceReference(uri="flare:result:M9-P3-AIRFLOW:calibrated_airflow_velocity_median")
            ],
        )
        res = validator.validate_claim(claim)
        assert res.validation_status == ClaimValidationStatus.REJECTED
        assert "Unit mismatch" in str(res.validation_error)

    def test_claim_sample_size_mismatch_rejected(self, validator):
        claim = ScientificClaim(
            claim_type=ClaimType.STATISTICAL_METRIC,
            subject_entity="ambient_initial_o2",
            claimed_statement="Initial oxygen tested on 50 samples.",
            metric_identifier="ambient_initial_o2_median",
            claimed_numeric_value=Decimal("0.21"),
            claimed_sample_size=50,  # Actual is 129
            evidence_references=[
                StableEvidenceReference(uri="flare:result:M9-P1-ENV-STATS:ambient_initial_o2_median")
            ],
        )
        res = validator.validate_claim(claim)
        assert res.validation_status == ClaimValidationStatus.REJECTED
        assert "Sample size mismatch" in str(res.validation_error)

    def test_claim_nonexistent_metric_rejected(self, validator):
        claim = ScientificClaim(
            claim_type=ClaimType.STATISTICAL_METRIC,
            subject_entity="hallucinated_variable",
            claimed_statement="Hallucinated metric is 99.9.",
            metric_identifier="non_existent_metric_code",
            claimed_numeric_value=Decimal("99.9"),
            evidence_references=[
                StableEvidenceReference(uri="flare:result:M9-FAKE:non_existent_metric_code")
            ],
        )
        res = validator.validate_claim(claim)
        assert res.validation_status == ClaimValidationStatus.REJECTED
        assert "not found in sealed M9" in str(res.validation_error)

    @pytest.mark.parametrize(
        "prohibited_text,expected_reason",
        [
            ("Calculating Biot number Bi = 0.05 for thin PMMA", "Biot number"),
            ("LOI regression indicates 18% flammability threshold", "Limiting Oxygen Index"),
            ("Extrapolating combustion to lunar gravity conditions", "lunar or Martian"),
            ("Predicted flame spread rate is 1.5 mm/s", "flame spread rate"),
            ("Fire risk odds ratio is 2.3", "Fire risk odds ratios"),
        ],
    )
    def test_prohibited_scientific_claims_rejected(self, validator, prohibited_text, expected_reason):
        claim = ScientificClaim(
            claim_type=ClaimType.METHODOLOGICAL_LIMITATION,
            subject_entity="Prohibited Concept",
            claimed_statement=prohibited_text,
            evidence_references=[StableEvidenceReference(uri="flare:test:PSI-25:mock")],
        )
        res = validator.validate_claim(claim)
        assert res.validation_status == ClaimValidationStatus.REJECTED
        assert expected_reason.lower() in str(res.validation_error).lower()


class TestScientificSynthesisService:
    """Test synthesis generation, provider degradation, and narrative invariant."""

    def test_nominal_synthesis_with_mock_provider(self):
        plan = create_execution_plan(
            question="What was the ambient initial oxygen concentration in BASS-II?",
            investigation="PSI-25",
        )
        tool_results = [
            ToolResult(
                tool_id="m9_get_analytical_result",
                execution_status=ToolExecutionStatus.SUCCESS,
                request_id=plan.request_id,
                result_data={
                    "metric_code": "ambient_initial_o2_median",
                    "protocol_code": "M9-P1-ENV-STATS",
                    "numeric_value": 0.21,
                    "unit": "mol/mol",
                    "sample_size": 129,
                    "ci_lower": 0.20,
                    "ci_upper": 0.22,
                },
                source_hash="71e792bf6b5fb5ea620c5dd70fbbac05515992e12aefcf5dff47312caa48c042",
            )
        ]

        canned = {
            "answer": "BASS-II tests exhibited a median initial oxygen mole fraction of 0.21 mol/mol.",
            "key_findings": ["Initial oxygen median is 0.21 mol/mol across 129 tests."],
            "scientific_claims": [
                {
                    "claim_type": "STATISTICAL_METRIC",
                    "subject_entity": "ambient_initial_o2",
                    "claimed_statement": "Median oxygen mole fraction was 0.21 mol/mol (N=129).",
                    "metric_identifier": "ambient_initial_o2_median",
                    "claimed_numeric_value": 0.21,
                    "claimed_unit": "mol/mol",
                    "claimed_sample_size": 129,
                    "evidence_references": [
                        {
                            "uri": "flare:result:M9-P1-ENV-STATS:ambient_initial_o2_median",
                            "evidence_type": "DQ",
                            "epistemic_status": "SUPPORTED",
                        }
                    ],
                }
            ],
            "uncertainty_and_limitations": ["95% CI order statistic is [0.20, 0.22]."],
            "epistemic_status": "SUPPORTED",
        }

        mock_p = MockLLMProvider(default_response=canned)
        service = ScientificSynthesisService(provider=mock_p)
        resp: SynthesizedResponse = service.synthesize(plan=plan, tool_results=tool_results)

        assert resp.epistemic_status == EpistemicStatus.SUPPORTED
        assert len(resp.scientific_claims) == 1
        assert resp.scientific_claims[0].validation_status == ClaimValidationStatus.VALIDATED
        assert resp.rejected_claims_count == 0
        assert "0.21" in resp.answer

    def test_narrative_invariant_filters_rejected_claim(self):
        """When an LLM produces an ungrounded or mismatched claim, it must be excluded."""
        plan = create_execution_plan(
            question="What was the ambient initial oxygen concentration in BASS-II?",
            investigation="PSI-25",
        )
        tool_results = [
            ToolResult(
                tool_id="m9_get_analytical_result",
                execution_status=ToolExecutionStatus.SUCCESS,
                request_id=plan.request_id,
                result_data={
                    "metric_code": "ambient_initial_o2_median",
                    "protocol_code": "M9-P1-ENV-STATS",
                    "numeric_value": 0.21,
                    "unit": "mol/mol",
                    "sample_size": 129,
                },
            )
        ]

        # LLM invents a hallucinated claim of 0.45
        canned = {
            "answer": "Test answer.",
            "key_findings": ["Finding"],
            "scientific_claims": [
                {
                    "claim_type": "STATISTICAL_METRIC",
                    "subject_entity": "ambient_initial_o2",
                    "claimed_statement": "Hallucinated oxygen of 0.45 mol/mol.",
                    "metric_identifier": "ambient_initial_o2_median",
                    "claimed_numeric_value": 0.45,  # Mismatch!
                    "evidence_references": [{"uri": "flare:result:M9-P1-ENV-STATS:ambient_initial_o2_median"}],
                }
            ],
            "uncertainty_and_limitations": [],
            "epistemic_status": "SUPPORTED",
        }

        mock_p = MockLLMProvider(default_response=canned)
        service = ScientificSynthesisService(provider=mock_p)
        resp = service.synthesize(plan=plan, tool_results=tool_results)

        # Invariant enforcement: Rejected claim MUST NOT be in scientific_claims
        assert len(resp.scientific_claims) == 0
        assert resp.rejected_claims_count == 1
        assert any("Numeric value mismatch" in lim for lim in resp.uncertainty_and_limitations)
        assert "excluded from verified findings" in resp.answer

    def test_provider_unavailable_falls_back_to_deterministic_synthesis(self):
        """When the LLM provider is offline, the system must degrade gracefully without 500 error."""
        plan = create_execution_plan(
            question="What was the ambient initial oxygen concentration in BASS-II?",
            investigation="PSI-25",
        )
        tool_results = [
            ToolResult(
                tool_id="m9_get_analytical_result",
                execution_status=ToolExecutionStatus.SUCCESS,
                request_id=plan.request_id,
                result_data={
                    "metric_code": "ambient_initial_o2_median",
                    "protocol_code": "M9-P1-ENV-STATS",
                    "numeric_value": 0.21,
                    "unit": "mol/mol",
                    "sample_size": 129,
                    "ci_lower": 0.20,
                    "ci_upper": 0.22,
                },
            )
        ]

        # Offline provider
        offline_p = MockLLMProvider(available=False)
        service = ScientificSynthesisService(provider=offline_p)
        resp = service.synthesize(plan=plan, tool_results=tool_results)

        assert resp.provider_status == "unavailable"
        assert len(resp.scientific_claims) == 1
        assert resp.scientific_claims[0].claimed_numeric_value == Decimal("0.21")
        assert resp.scientific_claims[0].validation_status == ClaimValidationStatus.VALIDATED
        assert any("LLM provider unavailable" in lim for lim in resp.uncertainty_and_limitations)
        assert "ambient_initial_o2_median" in resp.answer

    def test_prohibited_query_synthesizer_refusal(self):
        plan = create_execution_plan(
            question="Calculate the Biot number Bi << 0.1 for thin PMMA.",
            investigation="PSI-25",
        )
        tool_results = [
            ToolResult(
                tool_id="flare_check_scientific_prohibition",
                execution_status=ToolExecutionStatus.PROHIBITED,
                request_id=plan.request_id,
                limitations=["Biot number calculations are strictly prohibited."],
            )
        ]
        service = ScientificSynthesisService(provider=MockLLMProvider())
        resp = service.synthesize(plan=plan, tool_results=tool_results)

        assert resp.provider_status == "abstained"
        assert resp.epistemic_status == EpistemicStatus.UNRESOLVED
        assert len(resp.scientific_claims) == 0
        assert "Scientific Inquiry Refusal" in resp.answer
        assert any("prohibited" in lim.lower() for lim in resp.uncertainty_and_limitations)


class TestIntelligenceExecuteApiM105:
    """Test API integration of synthesis in POST /api/v1/intelligence/execute."""

    def test_api_execute_returns_synthesis_payload(self):
        mock_canned = {
            "answer": "Calibrated airflow velocity median across BASS-II is 2.45 cm/s.",
            "key_findings": ["Airflow median is 2.45 cm/s."],
            "scientific_claims": [],
            "uncertainty_and_limitations": ["Limited by duct anemometer calibration."],
            "epistemic_status": "SUPPORTED",
        }
        mock_p = MockLLMProvider(default_response=mock_canned)
        app.state.synthesis_service = ScientificSynthesisService(provider=mock_p)

        client = TestClient(app)
        response = client.post(
            "/api/v1/intelligence/execute",
            json={
                "question": "What was the calibrated airflow velocity across tests?",
                "synthesize": True,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "synthesis" in data
        assert data["synthesis"] is not None
        assert "Calibrated airflow velocity" in data["synthesis"]["answer"]
        assert data["synthesis"]["provider_status"] == "available"
