"""Authoritative Scientific Synthesis Service for FLARE M10.5.

Coordinates prompt assembly, provider invocation, fallback degradation,
and deterministic scientific claim validation.
"""
from __future__ import annotations

from decimal import Decimal
import json
import logging
import time
from typing import TYPE_CHECKING, Any

from app.intelligence.llm.base import BaseLLMProvider, ProviderUnavailableError
from app.intelligence.llm.factory import get_llm_provider
from app.intelligence.synthesis.prompt_builder import build_synthesis_prompt
from app.intelligence.synthesis.schemas import SynthesizedResponse
from app.intelligence.validation.claim_validator import ClaimValidator
from app.intelligence.validation.schemas import (
    ClaimType,
    ClaimValidationStatus,
    EpistemicStatus,
    EvidenceType,
    ScientificClaim,
    StableEvidenceReference,
)

if TYPE_CHECKING:
    from app.intelligence.schemas import ExecutionPlan
    from app.intelligence.tool_schemas import ToolResult

logger = logging.getLogger(__name__)


class ScientificSynthesisService:
    """Coordinates LLM synthesis with deterministic claim validation and fallback."""

    def __init__(self, provider: BaseLLMProvider | None = None) -> None:
        self._provider = provider

    def get_provider(self) -> BaseLLMProvider:
        if self._provider is None:
            self._provider = get_llm_provider()
        return self._provider

    def synthesize(
        self,
        plan: ExecutionPlan,
        tool_results: list[ToolResult],
    ) -> SynthesizedResponse:
        """Produce an evidence-grounded scientific synthesis for the executed plan."""
        from app.intelligence.schemas import QueryState, ScopeStatusEnum
        from app.intelligence.tool_schemas import ToolExecutionStatus
        start_time = time.perf_counter()

        # 1. Prohibited or Abstained Query Handling
        is_prohibited = (
            any(tr.execution_status == ToolExecutionStatus.PROHIBITED for tr in tool_results)
            or plan.scope_status == ScopeStatusEnum.PROHIBITED
            or bool(plan.abstention_reason and "prohibit" in plan.abstention_reason.lower())
        )
        is_abstained = (
            plan.state == QueryState.ABSTAINED
            or plan.scope_status in {ScopeStatusEnum.PROHIBITED, ScopeStatusEnum.OUT_OF_SCOPE, ScopeStatusEnum.AMBIGUOUS}
        )

        if is_prohibited or is_abstained:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            reasons = [plan.abstention_reason] if plan.abstention_reason else []
            for tr in tool_results:
                reasons.extend(tr.limitations)
            refusal_text = (
                "### Scientific Inquiry Refusal / Scope Boundary\n\n"
                "The requested query involves concepts that are strictly prohibited or outside "
                "the validated scientific operational boundary of FLARE.\n\n"
                "**Identified Constraints:**\n"
                + "\n".join(f"- {r}" for r in (reasons or ["Operation outside validated scope."]))
            )
            return SynthesizedResponse(
                answer=refusal_text,
                key_findings=[],
                scientific_claims=[],
                evidence_references=[],
                uncertainty_and_limitations=reasons or ["Prohibited or out of scope."],
                tools_used=[tr.tool_id for tr in tool_results],
                epistemic_status=EpistemicStatus.UNRESOLVED,
                provider_status="abstained",
                execution_duration_ms=round(duration_ms, 2),
            )

        # 2. Extract Sealed M9 Results and Literature Chunks for Grounding
        sealed_m9_results: dict[str, dict[str, Any]] = {}
        retrieved_docs: list[dict[str, Any]] = []
        evidence_refs: list[StableEvidenceReference] = []
        tools_used: list[str] = []

        for tr in tool_results:
            tools_used.append(tr.tool_id)
            if tr.tool_id == "m9_get_analytical_result":
                items = tr.result_data if isinstance(tr.result_data, list) else ([tr.result_data] if isinstance(tr.result_data, dict) else [])
                for item in items:
                    if isinstance(item, dict):
                        metric_code = item.get("metric_code")
                        if metric_code:
                            sealed_m9_results[metric_code] = item
                            # Add empirical evidence reference
                            protocol = item.get("protocol_code", "M9")
                            uri = f"flare:result:{protocol}:{metric_code}"
                            evidence_refs.append(
                                StableEvidenceReference(
                                    uri=uri,
                                    evidence_type=EvidenceType.DERIVED_QUANTITY,
                                    epistemic_status=EpistemicStatus.SUPPORTED,
                                    source_sha256=tr.source_hash,
                                    location_label=f"Analytical Result ({protocol})",
                                    summary_snippet=f"{metric_code}: {item.get('numeric_value')} {item.get('unit')}",
                                )
                            )
            elif tr.tool_id == "flare_retrieve_documents" and isinstance(tr.result_data, list):
                for chunk in tr.result_data:
                    retrieved_docs.append(chunk)
                    doc_id = chunk.get("doc_id", "doc")
                    p_start = chunk.get("page_start", 1)
                    uri = f"flare:doc:{chunk.get('source_hash', 'unknown')}:page={p_start}"
                    evidence_refs.append(
                        StableEvidenceReference(
                            uri=uri,
                            evidence_type=EvidenceType.REFERENCE_THEORETICAL,
                            epistemic_status=EpistemicStatus.SUPPORTED,
                            source_sha256=chunk.get("source_hash"),
                            location_label=f"{chunk.get('title', 'NASA Document')} (p. {p_start})",
                            summary_snippet=chunk.get("content_snippet", "")[:150],
                        )
                    )

        validator = ClaimValidator(
            sealed_m9_results=sealed_m9_results,
            retrieved_documents=retrieved_docs,
        )

        # 3. Attempt LLM Provider Invocation
        provider = self.get_provider()
        llm_raw_response: str | None = None
        provider_status = "available"
        provider_model = provider.model_name

        try:
            if not provider.is_available():
                raise ProviderUnavailableError(f"Provider {provider.provider_name} reported unavailable")

            system_prompt, user_prompt = build_synthesis_prompt(plan, tool_results)
            response = provider.generate_sync(
                prompt=user_prompt,
                system_prompt=system_prompt,
                response_format="json",
                temperature=0.1,
            )
            llm_raw_response = response.content
        except (ProviderUnavailableError, Exception) as exc:
            logger.warning("LLM provider invocation failed (%s). Falling back to deterministic synthesis.", exc)
            provider_status = "unavailable"
            llm_raw_response = None

        # 4. Process LLM Output or Fallback to Deterministic Assembly
        if llm_raw_response:
            try:
                parsed_json = self._parse_json_safely(llm_raw_response)
                validated_claims: list[ScientificClaim] = []
                rejected_count = 0
                collected_limitations = [plan.abstention_reason] if plan.abstention_reason else []

                for lim in parsed_json.get("uncertainty_and_limitations", []):
                    if isinstance(lim, str) and lim.strip():
                        collected_limitations.append(lim.strip())

                # Validate each draft claim
                draft_claims_raw = parsed_json.get("scientific_claims", [])
                rejected_values: set[str] = set()
                for dc in draft_claims_raw:
                    try:
                        claim_obj = self._build_claim_from_dict(dc)
                        validated_claim = validator.validate_claim(claim_obj)
                        if validated_claim.validation_status == ClaimValidationStatus.VALIDATED:
                            validated_claims.append(validated_claim)
                        else:
                            rejected_count += 1
                            if validated_claim.claimed_numeric_value is not None:
                                rejected_values.add(str(validated_claim.claimed_numeric_value))
                            if validated_claim.validation_error:
                                collected_limitations.append(
                                    f"Excluded unverified claim '{validated_claim.claimed_statement}': {validated_claim.validation_error}"
                                )
                    except Exception as err:
                        rejected_count += 1
                        logger.debug("Failed to build/validate draft claim: %s", err)

                answer_text = str(parsed_json.get("answer", "")).strip()
                if not answer_text:
                    answer_text = self._build_deterministic_answer(plan, sealed_m9_results, retrieved_docs)

                # Narrative Generation Constraint Invariant Notice
                if rejected_count > 0:
                    answer_text += (
                        "\n\n> [!NOTE]\n"
                        f"> {rejected_count} initial quantitative assertion(s) failed deterministic verification "
                        "against sealed ground truth and were excluded from verified findings."
                    )

                raw_findings = [str(f) for f in parsed_json.get("key_findings", []) if f]
                filtered_findings = [
                    f for f in raw_findings
                    if not any(rv in f for rv in rejected_values)
                ] if rejected_values else raw_findings

                duration_ms = (time.perf_counter() - start_time) * 1000.0
                return SynthesizedResponse(
                    answer=answer_text,
                    key_findings=filtered_findings,
                    scientific_claims=validated_claims,
                    evidence_references=evidence_refs,
                    uncertainty_and_limitations=collected_limitations,
                    tools_used=tools_used,
                    epistemic_status=EpistemicStatus(parsed_json.get("epistemic_status", "SUPPORTED")),
                    provider_status=provider_status,
                    provider_model=provider_model,
                    rejected_claims_count=rejected_count,
                    execution_duration_ms=round(duration_ms, 2),
                )
            except Exception as exc:
                logger.error("Failed to parse LLM JSON output (%s). Falling back to deterministic assembly.", exc)
                provider_status = "degraded"

        # 5. Deterministic Grounded Fallback (when LLM unavailable or fails JSON parsing)
        return self._generate_deterministic_fallback(
            plan=plan,
            sealed_m9_results=sealed_m9_results,
            retrieved_docs=retrieved_docs,
            evidence_refs=evidence_refs,
            tools_used=tools_used,
            provider_status=provider_status,
            provider_model=provider_model,
            start_time=start_time,
        )

    def _generate_deterministic_fallback(
        self,
        plan: ExecutionPlan,
        sealed_m9_results: dict[str, dict[str, Any]],
        retrieved_docs: list[dict[str, Any]],
        evidence_refs: list[StableEvidenceReference],
        tools_used: list[str],
        provider_status: str,
        provider_model: str | None,
        start_time: float,
    ) -> SynthesizedResponse:
        """Deterministic, rule-based scientific synthesis when LLM is offline or degraded."""
        answer_text = self._build_deterministic_answer(plan, sealed_m9_results, retrieved_docs)
        key_findings: list[str] = []
        verified_claims: list[ScientificClaim] = []
        limitations: list[str] = [plan.abstention_reason] if plan.abstention_reason else []

        if provider_status == "unavailable":
            limitations.append("LLM provider unavailable. Showing deterministic tool results directly.")

        # Build verified claims directly from M9 metrics
        for metric_code, mdata in sealed_m9_results.items():
            num_val = mdata.get("numeric_value")
            unit = mdata.get("unit")
            n = mdata.get("sample_size")
            ci_l = mdata.get("ci_lower")
            ci_u = mdata.get("ci_upper")
            protocol = mdata.get("protocol_code", "M9")

            key_findings.append(
                f"{metric_code}: {num_val} {unit} (N={n}, 95% CI: [{ci_l}, {ci_u}])"
            )
            claim = ScientificClaim(
                claim_type=ClaimType.STATISTICAL_METRIC,
                subject_entity=metric_code,
                claimed_statement=f"Deterministic analytical metric {metric_code} is {num_val} {unit} with N={n}.",
                claimed_numeric_value=Decimal(str(num_val)) if num_val is not None else None,
                claimed_unit=unit,
                metric_identifier=metric_code,
                claimed_ci_lower=Decimal(str(ci_l)) if ci_l is not None else None,
                claimed_ci_upper=Decimal(str(ci_u)) if ci_u is not None else None,
                claimed_sample_size=n,
                evidence_references=[
                    StableEvidenceReference(
                        uri=f"flare:result:{protocol}:{metric_code}",
                        evidence_type=EvidenceType.DERIVED_QUANTITY,
                        epistemic_status=EpistemicStatus.SUPPORTED,
                        location_label=f"Analytical Result ({protocol})",
                        summary_snippet=f"Deterministic value: {num_val} {unit}",
                    )
                ],
                validation_status=ClaimValidationStatus.VALIDATED,
                epistemic_verdict=EpistemicStatus.SUPPORTED,
            )
            verified_claims.append(claim)

        # If literature passages exist, highlight them in key findings
        for doc in retrieved_docs[:3]:
            title = doc.get("title", "NASA Document")
            p_start = doc.get("page_start", 1)
            snippet = doc.get("content_snippet", "")[:120]
            key_findings.append(f"{title} (p. {p_start}): \"{snippet}...\"")

        duration_ms = (time.perf_counter() - start_time) * 1000.0
        return SynthesizedResponse(
            answer=answer_text,
            key_findings=key_findings,
            scientific_claims=verified_claims,
            evidence_references=evidence_refs,
            uncertainty_and_limitations=limitations,
            tools_used=tools_used,
            epistemic_status=EpistemicStatus.SUPPORTED if (verified_claims or retrieved_docs) else EpistemicStatus.UNRESOLVED,
            provider_status=provider_status,
            provider_model=provider_model,
            rejected_claims_count=0,
            execution_duration_ms=round(duration_ms, 2),
        )

    def _build_deterministic_answer(
        self,
        plan: ExecutionPlan,
        sealed_m9_results: dict[str, dict[str, Any]],
        retrieved_docs: list[dict[str, Any]],
    ) -> str:
        """Construct a formatted markdown answer from tool results."""
        lines: list[str] = [
            f"### Scientific Synthesis: {plan.original_question}\n",
        ]

        if sealed_m9_results:
            lines.append("#### Deterministic Quantitative Metrics (M9 Engine)")
            lines.append(
                "The following metrics were computed deterministically by the FLARE scientific engine "
                f"and verified against cryptographically sealed flight datasets ({plan.investigation}):\n"
            )
            for code, m in sealed_m9_results.items():
                ci = f"[{m.get('ci_lower')}, {m.get('ci_upper')}]" if m.get('ci_lower') is not None else "N/A"
                lines.append(
                    f"- **`{code}`**: `{m.get('numeric_value')} {m.get('unit')}`  \n"
                    f"  *Sample Size*: N={m.get('sample_size')} | *95% Confidence Interval*: {ci} | *Protocol*: `{m.get('protocol_code')}`"
                )
            lines.append("")

        if retrieved_docs:
            lines.append("#### Grounded NASA Literature Passages")
            lines.append(
                "The following passages were retrieved from registered NASA mission documentation:\n"
            )
            for idx, doc in enumerate(retrieved_docs[:3], 1):
                title = doc.get("title", "NASA Source Document")
                page_str = f"Page {doc.get('page_start')}" if doc.get('page_start') else ""
                lines.append(f"**{idx}. {title}** ({page_str})")
                lines.append(f"> \"{doc.get('content_snippet', '').strip()}\"\n")

        if not sealed_m9_results and not retrieved_docs:
            lines.append(
                "No matching quantitative analytical results or literature passages were identified "
                "for the specified query within the FLARE flight repository."
            )

        return "\n".join(lines)

    @staticmethod
    def _parse_json_safely(raw: str) -> dict[str, Any]:
        """Strip markdown fences and parse JSON robustly."""
        cleaned = raw.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        return json.loads(cleaned)

    @staticmethod
    def _build_claim_from_dict(d: dict[str, Any]) -> ScientificClaim:
        """Convert a draft JSON dictionary from LLM into a ScientificClaim object."""
        ev_refs: list[StableEvidenceReference] = []
        for ev in d.get("evidence_references", []):
            if isinstance(ev, dict) and ev.get("uri"):
                ev_refs.append(
                    StableEvidenceReference(
                        uri=str(ev.get("uri")),
                        evidence_type=EvidenceType(ev.get("evidence_type", "EM")),
                        epistemic_status=EpistemicStatus(ev.get("epistemic_status", "SUPPORTED")),
                        source_sha256=ev.get("source_sha256"),
                        location_label=str(ev.get("location_label", "")),
                        summary_snippet=str(ev.get("summary_snippet", "")),
                    )
                )

        num_val = d.get("claimed_numeric_value")
        ci_l = d.get("claimed_ci_lower")
        ci_u = d.get("claimed_ci_upper")

        return ScientificClaim(
            claim_type=ClaimType(d.get("claim_type", "STATISTICAL_METRIC")),
            subject_entity=str(d.get("subject_entity", "unknown")),
            claimed_statement=str(d.get("claimed_statement", "")),
            claimed_numeric_value=Decimal(str(num_val)) if num_val is not None else None,
            claimed_unit=str(d.get("claimed_unit")) if d.get("claimed_unit") else None,
            metric_identifier=str(d.get("metric_identifier")) if d.get("metric_identifier") else None,
            claimed_ci_lower=Decimal(str(ci_l)) if ci_l is not None else None,
            claimed_ci_upper=Decimal(str(ci_u)) if ci_u is not None else None,
            claimed_sample_size=int(d["claimed_sample_size"]) if d.get("claimed_sample_size") is not None else None,
            evidence_references=ev_refs,
        )
