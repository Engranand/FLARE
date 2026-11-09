"""Lexical categories only: no quantities, units or physical meanings are inferred."""
from typing import Literal
import re

Classification = Literal["numeric", "negative_numeric", "empty", "literal_none",
                         "censored_numeric", "ambiguous_token", "compound_text", "other_text"]
CATEGORIES: tuple[Classification, ...] = (
    "numeric", "negative_numeric", "empty", "literal_none", "censored_numeric",
    "ambiguous_token", "compound_text", "other_text",
)
NUMBER = r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?"
# Only unambiguous numeric sequences are labelled compound. Dates, dimensions and
# annotated settings conservatively fall back to other_text without semantic guesses.
SEQUENCE = re.compile(rf"{NUMBER}(?:(?:\s+|\s*[;,>]\s*){NUMBER})+")


def classify(raw: str) -> tuple[Classification, list[str]]:
    value = raw.strip()
    flags = ["classification_whitespace_normalized"] if value != raw else []
    if raw == "":
        category: Classification = "empty"
    elif value == "":
        category = "other_text"
        flags.append("whitespace_only_not_empty")
    elif value == "none":
        category = "literal_none"
    elif value in {"OR", "over"}:
        category = "ambiguous_token"
    elif re.fullmatch(NUMBER, value):
        category = "negative_numeric" if value.startswith("-") else "numeric"
    elif re.fullmatch(rf"(?:<=|>=|<|>)\s*{NUMBER}", value):
        category = "censored_numeric"
    elif SEQUENCE.fullmatch(value):
        category = "compound_text"
    else:
        category = "other_text"
    if category != "numeric":
        flags.append({
            "empty": "empty_source_cell", "literal_none": "literal_none_preserved",
            "negative_numeric": "negative_sign_preserved",
            "censored_numeric": "censored_not_exact", "ambiguous_token": "unresolved_token",
            "compound_text": "sequence_structure_uninterpreted", "other_text": "unclassified_text_review",
        }[category])
    return category, flags
