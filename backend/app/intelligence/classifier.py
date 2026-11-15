"""Deterministic Intent Classification for FLARE Milestone 10.2 Intelligence Engine.

NOTE ON METHODOLOGY:
This module utilizes deterministic pattern matching and rule-based heuristics for the
initial M10.2 orchestration pipeline. It does NOT employ an LLM or pretend that keyword
matching constitutes deep semantic natural-language comprehension. All rules are explicit,
reproducible, and fully transparent.

Supported Intents:
1. SCIENTIFIC_ANALYSIS: Quantitative queries for M9 statistical metrics, medians, IQRs, depletion, airflow, morphology.
2. OBSERVATION_LOOKUP: Queries for specific test run records, individual sensor readings, or raw observation rows.
3. DOCUMENT_RETRIEVAL: Queries seeking authentic NASA technical reports, README files, FAQs, or literature citations.
4. COMBINED_RESEARCH: Queries requiring both quantitative analytical data and qualitative literature context.
5. SCIENTIFIC_EXPLANATION: Conceptual or mechanistic inquiries into microgravity combustion physics.
6. OUT_OF_SCOPE: Inquiries unrelated to spacecraft fire safety or microgravity science.
7. AMBIGUOUS: Underspecified, truncated, or excessively vague queries.
"""
from __future__ import annotations

import re

from app.intelligence.schemas import IntentEnum, ScopeStatusEnum
from app.intelligence.scope_gate import evaluate_scope

# Keyword/Regex definitions for deterministic classification
_OBSERVATION_PATTERNS = [
    re.compile(r"\btest[_\s-]?0?([1-9][0-9]?|1[0-2][0-9])\b", re.IGNORECASE),  # test_01 to test_129
    re.compile(r"\b(raw\s+observations?|observation\s+records?|csv\s+rows?|sensor\s+logs?)\b", re.IGNORECASE),
    re.compile(r"\b(what\s+happened\s+in\s+test|specific\s+runs?|flight\s+records?)\b", re.IGNORECASE),
]

_DOCUMENT_PATTERNS = [
    re.compile(r"\b(papers?|technical\s+reports?|readmes?|faqs?|documents?|literature|citations?|cites?|references?|manuals?|handbooks?)\b", re.IGNORECASE),
    re.compile(r"\b(who\s+wrote|who\s+is\s+the\s+author|published|journals?|conferences?)\b", re.IGNORECASE),
]

_ANALYSIS_PATTERNS = [
    re.compile(r"\b(medians?|iqrs?|interquartiles?|confidence\s+intervals?|order\s+statistics?)\b", re.IGNORECASE),
    re.compile(r"\b(oxygen\s+depletions?|o2\s+depletions?|relative\s+depletions?|depletion\s+ratios?)\b", re.IGNORECASE),
    re.compile(r"\b(initial\s+o2|initial\s+co2|initial\s+co|ambient\s+o2|ambient\s+gas)\b", re.IGNORECASE),
    re.compile(r"\b(calibrated\s+airflow|airflow\s+velocity|flow\s+speed|duct\s+velocity)\b", re.IGNORECASE),
    re.compile(r"\b(fuel\s+morphology|regimes?|specimen\s+counts?|unique\s+specimens?|first\s+burns?|reburns?)\b", re.IGNORECASE),
    re.compile(r"\b(how\s+much\s+o2|what\s+is\s+the\s+average|statistical\s+summary|m9\s+metrics?)\b", re.IGNORECASE),
]

_EXPLANATION_PATTERNS = [
    re.compile(r"\b(why\s+does|how\s+does|explain\s+the\s+mechanism|phenomenon|physics\s+of)\b", re.IGNORECASE),
    re.compile(r"\b(quiescent|radiation\s+loss|flame\s+standoff|soot\s+shell|buoyancy\s+suppression)\b", re.IGNORECASE),
    re.compile(r"\b(extinction\s+mechanism|forced\s+convection\s+effect|microgravity\s+effect)\b", re.IGNORECASE),
    re.compile(r"\b(what\s+nasa\s+experiments|what\s+experiments\s+investigated|differences?\s+(were\s+)?observed|experimental\s+conditions?)\b", re.IGNORECASE),
    re.compile(r"\b(solid[- ]fuel\s+flammability|flammability\s+limits?|flame\s+behaviour|flame\s+behavior)\b", re.IGNORECASE),
]


def classify_intent(normalized_question: str) -> IntentEnum:
    """Classify the intent of a normalized question using deterministic rules.
    
    Args:
        normalized_question: Sanitized, whitespace-normalized question string.
        
    Returns:
        IntentEnum indicating the classified intent category.
    """
    # 1. Gate against scope status first
    scope_status, _ = evaluate_scope(normalized_question)
    if scope_status == ScopeStatusEnum.OUT_OF_SCOPE:
        return IntentEnum.OUT_OF_SCOPE
    if scope_status == ScopeStatusEnum.AMBIGUOUS:
        return IntentEnum.AMBIGUOUS

    # 2. Check pattern matches
    has_observation = any(p.search(normalized_question) for p in _OBSERVATION_PATTERNS)
    has_document = any(p.search(normalized_question) for p in _DOCUMENT_PATTERNS)
    has_analysis = any(p.search(normalized_question) for p in _ANALYSIS_PATTERNS)
    has_explanation = any(p.search(normalized_question) for p in _EXPLANATION_PATTERNS)

    # 3. Disambiguate multi-category matches
    if (has_analysis or has_observation) and has_document:
        return IntentEnum.COMBINED_RESEARCH

    if has_observation:
        return IntentEnum.OBSERVATION_LOOKUP

    if has_analysis:
        return IntentEnum.SCIENTIFIC_ANALYSIS

    if has_document:
        return IntentEnum.DOCUMENT_RETRIEVAL

    if has_explanation:
        return IntentEnum.SCIENTIFIC_EXPLANATION

    # 4. Fallback: if it discusses general combustion/spacecraft topics without specific metric keywords
    if re.search(r"\b(flame|flames|flammability|burn|burning|combustion|fire|bass|saffire|spacecraft|microgravity|fuel|fuels|airflow)\b", normalized_question, re.IGNORECASE):
        # Questions asking what/why/how default to explanation, otherwise scientific analysis
        if re.search(r"^(what|why|how)\b", normalized_question, re.IGNORECASE):
            return IntentEnum.SCIENTIFIC_EXPLANATION
        return IntentEnum.SCIENTIFIC_ANALYSIS

    return IntentEnum.AMBIGUOUS
