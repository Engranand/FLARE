"""Scientific Scope Gate and Security Boundary Enforcement for FLARE Milestone 10.2.

Enforces strict domain boundaries, security invariants, and scientific prohibitions:
- Prohibits arbitrary SQL generation or script injection
- Prohibits unsupported scientific extrapolations (Biot numbers, RQ_comb, slab LOI, lunar/Martian gravity, etc.)
- Segregates queries into ALLOWED, PROHIBITED, AMBIGUOUS, and OUT_OF_SCOPE statuses
- Provides authoritative, scientifically defensible explanations for all rejections
"""
from __future__ import annotations

import re

from app.intelligence.schemas import ScopeStatusEnum

# --- Security Invariant Patterns ---
_SQL_INJECTION_PATTERNS = [
    re.compile(r"\bselect\s+.+\s+from\b", re.IGNORECASE),
    re.compile(r"\binsert\s+into\b", re.IGNORECASE),
    re.compile(r"\bupdate\s+.+\s+set\b", re.IGNORECASE),
    re.compile(r"\bdelete\s+from\b", re.IGNORECASE),
    re.compile(r"\bdrop\s+(table|database|schema|view)\b", re.IGNORECASE),
    re.compile(r"\balter\s+table\b", re.IGNORECASE),
    re.compile(r"\btruncate\s+table\b", re.IGNORECASE),
    re.compile(r"\bunion\s+(all\s+)?select\b", re.IGNORECASE),
    re.compile(r"\bor\s+['\"]?1['\"]?\s*=\s*['\"]?1['\"]?", re.IGNORECASE),
    re.compile(r"--\s*", re.IGNORECASE),
    re.compile(r";\s*(select|drop|insert|update|delete)\b", re.IGNORECASE),
]

_CODE_INJECTION_PATTERNS = [
    re.compile(r"\beval\s*\(", re.IGNORECASE),
    re.compile(r"\bexec\s*\(", re.IGNORECASE),
    re.compile(r"__import__", re.IGNORECASE),
    re.compile(r"\bsubprocess\b", re.IGNORECASE),
    re.compile(r"\bos\.system\b", re.IGNORECASE),
    re.compile(r"\bimport\s+(os|sys|subprocess|shutil)\b", re.IGNORECASE),
]

# --- Scientific Prohibition Definitions ---
# Each prohibition maps to regex triggers and an authoritative rationale.
_SCIENTIFIC_PROHIBITIONS = [
    (
        "Biot Number",
        [
            re.compile(r"\bbiot\b", re.IGNORECASE),
            re.compile(r"\bbi\s*(<<|>>|<=|>=|<|>|=)\s*0?\.?1\b", re.IGNORECASE),
            re.compile(r"thermally\s+(thin|thick)\s+(classification|regime|assumption)", re.IGNORECASE),
        ],
        (
            "Biot number calculations (Bi << 0.1 or Bi >> 1) are scientifically prohibited in "
            "FLARE M9/M10 because thermal conductivity (k), surface heat transfer coefficient (h), "
            "and solid thermal properties are unverified in NASA BASS-II records."
        ),
    ),
    (
        "Combustion Quotient RQ_comb",
        [
            re.compile(r"\brq_comb\b", re.IGNORECASE),
            re.compile(r"\brq\s+comb\b", re.IGNORECASE),
            re.compile(r"respiratory\s+quotient", re.IGNORECASE),
            re.compile(r"combustion\s+quotient", re.IGNORECASE),
            re.compile(r"delta\s*co2\s*/\s*(-?delta\s*o2)", re.IGNORECASE),
        ],
        (
            "Combustion respiratory quotient (RQ_comb = delta CO2 / -delta O2) is deferred and prohibited "
            "because transient chamber CO2 and O2 measurements lack verified co-temporal sensor alignment "
            "and stoichiometric equivalence in BASS-II unvented burns."
        ),
    ),
    (
        "Slab LOI Regression / Extrapolation",
        [
            re.compile(r"slab\s+loi", re.IGNORECASE),
            re.compile(r"thick\s+slab\s+loi", re.IGNORECASE),
            re.compile(r"logistic\s+regression\s+(loi|extinction)", re.IGNORECASE),
            re.compile(r"extrapolat\w*\s+loi", re.IGNORECASE),
        ],
        (
            "Thick slab Limiting Oxygen Index (LOI) logistic regression is prohibited. "
            "PMMA slab extinguishments in BASS-II occurred under forced airflow flame-blowoff "
            "conditions rather than stagnant LOI equilibrium."
        ),
    ),
    (
        "Flame Spread Rate (V_f)",
        [
            re.compile(r"flame\s+spread\s+rate", re.IGNORECASE),
            re.compile(r"flame\s+spread\s+velocity", re.IGNORECASE),
            re.compile(r"rate\s+of\s+flame\s+spread", re.IGNORECASE),
            re.compile(r"\bv_f\b", re.IGNORECASE),
        ],
        (
            "Flame spread rate (V_f) calculations are not supported from tabular BASS-II data "
            "because spatial video tracking coordinates and camera calibration timestamps were not ingested."
        ),
    ),
    (
        "Absolute Molar Oxygen Consumption (delta n_O2)",
        [
            re.compile(r"molar\s+consumption", re.IGNORECASE),
            re.compile(r"absolute\s+o2\s+consumption", re.IGNORECASE),
            re.compile(r"delta\s+n_o2", re.IGNORECASE),
            re.compile(r"total\s+moles\s+of\s+o2", re.IGNORECASE),
        ],
        (
            "Absolute molar consumption (delta n_O2) cannot be derived because microgravity chamber volume "
            "(approx 90 L) pressure logs and absolute temperature transients are not calibrated in BASS-II observations."
        ),
    ),
    (
        "Cubic Flow Polynomial",
        [
            re.compile(r"cubic\s+flow", re.IGNORECASE),
            re.compile(r"cubic\s+polynomial", re.IGNORECASE),
            re.compile(r"third\s+order\s+flow", re.IGNORECASE),
        ],
        (
            "Cubic flow polynomials are prohibited. Calibrated airflow velocity in BASS-II must strictly "
            "follow the quadratic nozzle calibration curve or piecewise linear interpolation specified in M9-P3."
        ),
    ),
    (
        "Lunar / Martian Partial Gravity Extrapolation",
        [
            re.compile(r"lunar\s+gravity", re.IGNORECASE),
            re.compile(r"martian\s+gravity", re.IGNORECASE),
            re.compile(r"mars\s+fire", re.IGNORECASE),
            re.compile(r"moon\s+fire", re.IGNORECASE),
            re.compile(r"partial\s+gravity\s+extrapolation", re.IGNORECASE),
        ],
        (
            "Extrapolation to partial gravity environments (Lunar 1/6 g or Martian 3/8 g) is scientifically "
            "unsupported because BASS-II microgravity tests were conducted strictly aboard the ISS (10^-6 g) with forced convective flow."
        ),
    ),
    (
        "Fire-Risk Odds Ratios",
        [
            re.compile(r"odds\s+ratio", re.IGNORECASE),
            re.compile(r"fire\s+risk\s+odds", re.IGNORECASE),
            re.compile(r"logistic\s+odds\s+ratio", re.IGNORECASE),
            re.compile(r"relative\s+fire\s+risk", re.IGNORECASE),
        ],
        (
            "Fire-risk odds ratios are prohibited due to sample size constraints and non-randomized, "
            "convenience-sampled flight matrix protocol."
        ),
    ),
]

# --- Out-of-Scope Patterns ---
_OUT_OF_SCOPE_PATTERNS = [
    re.compile(r"\b(weather|forecast|temperature in new york|rain tomorrow|climate in)\b", re.IGNORECASE),
    re.compile(r"\b(recipes?|how to cook|bake|baking|cake|pizza|food|restaurants?)\b", re.IGNORECASE),
    re.compile(r"\b(stock price|crypto|bitcoin|investing|wall street|nasdaq|dow jones)\b", re.IGNORECASE),
    re.compile(r"\b(sports|football|basketball|soccer score|world cup|olympics|baseball)\b", re.IGNORECASE),
    re.compile(r"\b(who won the election|political party|president of|prime minister|senator)\b", re.IGNORECASE),
    re.compile(r"\b(movie review|celebrity|hollywood|pop song|actor|actress)\b", re.IGNORECASE),
]

# --- Ambiguous Patterns ---
_AMBIGUOUS_PATTERNS = [
    re.compile(r"^(what|why|how|tell me|explain|fire|flame|combustion|test|bass)\??$", re.IGNORECASE),
    re.compile(r"^what is this\??$", re.IGNORECASE),
    re.compile(r"^tell me more\??$", re.IGNORECASE),
    re.compile(r"^tell me about fire\??$", re.IGNORECASE),
    re.compile(r"^what happened\??$", re.IGNORECASE),
    re.compile(r"^run analysis\??$", re.IGNORECASE),
]


def evaluate_scope(normalized_question: str) -> tuple[ScopeStatusEnum, str | None]:
    """Evaluate whether an incoming query complies with scientific and operational boundaries.
    
    Args:
        normalized_question: Sanitized query string.
        
    Returns:
        A tuple of (ScopeStatusEnum, rationale_or_none).
    """
    # 1. Security Invariant: SQL Injection Check
    for pattern in _SQL_INJECTION_PATTERNS:
        if pattern.search(normalized_question):
            return (
                ScopeStatusEnum.PROHIBITED,
                "Security violation: Potential SQL injection or query manipulation detected. "
                "Arbitrary SQL queries are strictly prohibited."
            )

    # 2. Security Invariant: Arbitrary Code Injection Check
    for pattern in _CODE_INJECTION_PATTERNS:
        if pattern.search(normalized_question):
            return (
                ScopeStatusEnum.PROHIBITED,
                "Security violation: Potential arbitrary code execution detected. "
                "Execution of scripts or commands is strictly prohibited."
            )

    # 3. Scientific Prohibitions Check
    for name, patterns, explanation in _SCIENTIFIC_PROHIBITIONS:
        for pat in patterns:
            if pat.search(normalized_question):
                return (ScopeStatusEnum.PROHIBITED, explanation)

    # 4. Out-of-Scope Check
    for pat in _OUT_OF_SCOPE_PATTERNS:
        if pat.search(normalized_question):
            return (
                ScopeStatusEnum.OUT_OF_SCOPE,
                "Query is outside the scope of FLARE. FLARE specializes exclusively in spacecraft fire safety, "
                "microgravity combustion, and NASA BASS-II experimental analysis."
            )

    # 5. Ambiguity Check
    for pat in _AMBIGUOUS_PATTERNS:
        if pat.match(normalized_question.strip()):
            return (
                ScopeStatusEnum.AMBIGUOUS,
                "Query is too ambiguous or underspecified to generate a deterministic execution plan. "
                "Please specify target materials (e.g. PMMA flat, PMMA rod, Cotton-fiberglass), "
                "variables (e.g. initial O2, relative depletion, airflow velocity), or test run numbers."
            )

    # If word count is very low (e.g. <= 2 words) and doesn't contain a specific keyword
    tokens = normalized_question.strip().split()
    if len(tokens) <= 2:
        # Check if it mentions a test number or specific metric
        has_specific = bool(re.search(r"\b(test[_\s-]?\d+|psi-25|bass|pmma|nomex|airflow|oxygen)\b", normalized_question, re.IGNORECASE))
        if not has_specific:
            return (
                ScopeStatusEnum.AMBIGUOUS,
                "Query is too brief or ambiguous. Please provide more context regarding the target experiment, "
                "metric, or combustion research topic."
            )

    return (ScopeStatusEnum.ALLOWED, None)
