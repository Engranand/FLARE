"""Deterministic query normalization for FLARE Milestone 10.2 Intelligence Engine.

Provides input sanitization, whitespace normalization, and boundary enforcement:
- Rejects empty, whitespace-only, and out-of-bounds input
- Collapses multi-line, tabbed, and repetitive whitespace into single spaces
- Preserves both original raw question and normalized representation
"""
from __future__ import annotations

from dataclasses import dataclass
import re

from app.intelligence.schemas import QueryNormalizationError

MIN_QUERY_LENGTH = 3
MAX_QUERY_LENGTH = 1000

# Regular expression to collapse multiple consecutive whitespace characters
_WHITESPACE_COLLAPSE_RE = re.compile(r"\s+")


@dataclass(frozen=True)
class NormalizedQuery:
    """Immutable pair containing original raw query and sanitized query."""
    original: str
    normalized: str


def normalize_query(
    question: str,
    min_length: int = MIN_QUERY_LENGTH,
    max_length: int = MAX_QUERY_LENGTH,
) -> NormalizedQuery:
    """Sanitize and normalize an incoming natural-language question.
    
    Args:
        question: The raw user-supplied question string.
        min_length: Minimum permissible character count after whitespace stripping.
        max_length: Maximum permissible character count after whitespace stripping.
        
    Returns:
        NormalizedQuery containing original and collapsed strings.
        
    Raises:
        QueryNormalizationError: If question is empty, whitespace-only, or out of length bounds.
    """
    if not isinstance(question, str):
        raise QueryNormalizationError(f"Question must be a string, received {type(question).__name__}")

    raw_stripped = question.strip()
    if not raw_stripped:
        raise QueryNormalizationError("Question cannot be empty or whitespace-only.")

    # Collapse all whitespace sequences (spaces, tabs, newlines, carriage returns) to a single space
    collapsed = _WHITESPACE_COLLAPSE_RE.sub(" ", raw_stripped)

    char_len = len(collapsed)
    if char_len < min_length:
        raise QueryNormalizationError(
            f"Question is too short ({char_len} characters). Minimum required is {min_length}."
        )

    if char_len > max_length:
        raise QueryNormalizationError(
            f"Question exceeds maximum length limit ({char_len} > {max_length} characters)."
        )

    return NormalizedQuery(original=question, normalized=collapsed)
