"""Grounding prompt builder for LLM scientific synthesis (M10.5)."""
from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.intelligence.schemas import ExecutionPlan
    from app.intelligence.tool_schemas import ToolResult

SYSTEM_PROMPT = """You are the FLARE Scientific Intelligence Engine, an expert assistant for spacecraft fire safety and microgravity combustion physics.
Your role is to formulate strictly evidence-grounded scientific answers using ONLY the provided deterministic tool outputs and retrieved NASA literature passages.

CRITICAL SCIENTIFIC GROUNDING INVARIANTS:
1. MATHEMATICAL TRUTH: Never invent, estimate, calculate, or hallucinate numerical measurements, sample sizes, or confidence intervals. Every quantitative metric MUST match an exact value from the "DETERMINISTIC M9 ANALYTICAL RESULTS" section.
2. EVIDENCE CITATIONS: Only cite provided evidence references. Every claim must carry a stable URI starting with "flare:".
3. LITERATURE PASSAGES: Passages from the "RETRIEVED NASA LITERATURE PASSAGES" section provide qualitative explanations and scientific context. Never treat qualitative document excerpts as newly validated quantitative measurements.
4. TAXONOMY:
   - Experimental Measurements: marked as "EM"
   - Derived Quantities: marked as "DQ"
   - Reference/Theoretical: marked as "RT"
   - Numerical Simulations: marked as "NS" (mandatory badge [SIMULATION])
5. STRICT PROHIBITIONS:
   - Do NOT calculate Biot numbers.
   - Do NOT regress Limiting Oxygen Index (LOI) on fuel slabs.
   - Do NOT extrapolate combustion behavior to lunar or Martian gravity.
   - Do NOT predict flame-spread rate or propagation speed.
   - Do NOT calculate fire risk odds ratios.
   If the user asks about any of these prohibited topics, explicitly state that they are prohibited by FLARE scientific constraints.

OUTPUT FORMAT:
You MUST respond with a single valid JSON object adhering to this exact structure:
{
  "answer": "Detailed markdown explanation synthesizing the findings...",
  "key_findings": [
    "Clear bullet point 1",
    "Clear bullet point 2"
  ],
  "scientific_claims": [
    {
      "claim_type": "STATISTICAL_METRIC",
      "subject_entity": "Exact parameter or variable name",
      "claimed_statement": "Statement describing the metric",
      "metric_identifier": "exact_m9_metric_code",
      "claimed_numeric_value": 0.21,
      "claimed_unit": "mol/mol",
      "claimed_sample_size": 129,
      "evidence_references": [
        {
          "uri": "flare:result:M9-P1-ENV-STATS:exact_m9_metric_code",
          "evidence_type": "DQ",
          "epistemic_status": "SUPPORTED",
          "location_label": "BASS-II Flight Telemetry",
          "summary_snippet": "Median initial oxygen mole fraction"
        }
      ]
    }
  ],
  "uncertainty_and_limitations": [
    "Limitation 1 regarding experimental flight conditions or sensor limits"
  ],
  "epistemic_status": "SUPPORTED"
}
"""


def build_synthesis_prompt(
    plan: ExecutionPlan,
    tool_results: list[ToolResult],
) -> tuple[str, str]:
    """Construct (system_prompt, user_prompt) grounded in empirical and literature tool results."""
    m9_metrics: list[dict[str, Any]] = []
    observations: list[dict[str, Any]] = []
    literature_chunks: list[dict[str, Any]] = []
    collected_limitations: list[str] = [plan.abstention_reason] if plan.abstention_reason else []

    for tr in tool_results:
        collected_limitations.extend(tr.limitations)
        if tr.tool_id == "m9_get_analytical_result":
            items = tr.result_data if isinstance(tr.result_data, list) else ([tr.result_data] if isinstance(tr.result_data, dict) else [])
            for item in items:
                if isinstance(item, dict):
                    m9_metrics.append(item)
        elif tr.tool_id == "flare_query_observations" and isinstance(tr.result_data, dict):
            obs_rows = tr.result_data.get("rows", [])
            observations.extend(obs_rows[:10])  # limit prompt clutter to top 10 representative rows
        elif tr.tool_id == "flare_retrieve_documents" and isinstance(tr.result_data, list):
            literature_chunks.extend(tr.result_data[:5])  # top 5 literature passages

    user_sections: list[str] = [
        f"USER QUESTION: {plan.original_question}",
        f"CLASSIFIED INTENT: {plan.intent.value if hasattr(plan.intent, 'value') else plan.intent}",
        f"TARGET INVESTIGATION: {plan.investigation}",
    ]

    # Section 1: Deterministic M9 Analytical Results
    if m9_metrics:
        user_sections.append("\n=== DETERMINISTIC M9 ANALYTICAL RESULTS (GROUND TRUTH) ===")
        for m in m9_metrics:
            ci_str = f"[{m.get('ci_lower')}, {m.get('ci_upper')}]" if m.get('ci_lower') is not None else "N/A"
            user_sections.append(
                f"- Protocol: {m.get('protocol_code')}\n"
                f"  Metric: {m.get('metric_code')}\n"
                f"  Value: {m.get('numeric_value')} {m.get('unit')}\n"
                f"  Sample Size N: {m.get('sample_size')}\n"
                f"  95% Confidence Interval: {ci_str}\n"
                f"  Evidence URI: flare:result:{m.get('protocol_code')}:{m.get('metric_code')}\n"
                f"  Quality Flags: {', '.join(m.get('quality_flags', [])) or 'None'}"
            )
    else:
        user_sections.append("\n=== DETERMINISTIC M9 ANALYTICAL RESULTS ===\nNo quantitative M9 metrics available for this query.")

    # Section 2: Retrieved NASA Literature Passages
    if literature_chunks:
        user_sections.append("\n=== RETRIEVED NASA LITERATURE PASSAGES ===")
        for idx, chunk in enumerate(literature_chunks, 1):
            pages_str = f"pp. {chunk.get('page_start')}-{chunk.get('page_end')}" if chunk.get('page_start') else "N/A"
            user_sections.append(
                f"Passage {idx}:\n"
                f"  Document Title: {chunk.get('title')}\n"
                f"  Document ID: {chunk.get('doc_id')}\n"
                f"  Pages: {pages_str}\n"
                f"  Section: {chunk.get('section', 'Main')}\n"
                f"  Source SHA-256: {chunk.get('source_hash')}\n"
                f"  Evidence Type: {chunk.get('evidence_type', 'reference_information')}\n"
                f"  Excerpt: {chunk.get('content_snippet', '')}"
            )
    else:
        user_sections.append("\n=== RETRIEVED NASA LITERATURE PASSAGES ===\nNo literature passages retrieved for this query.")

    # Section 3: Empirical Limitations
    if collected_limitations:
        user_sections.append("\n=== EXPERIMENTAL & METHODOLOGICAL LIMITATIONS ===")
        for lim in set(collected_limitations):
            user_sections.append(f"- {lim}")

    user_sections.append(
        "\nSynthesize a rigorous scientific response in JSON format. Ensure all claims link to provided evidence URIs."
    )

    user_prompt = "\n".join(user_sections)
    return SYSTEM_PROMPT, user_prompt
