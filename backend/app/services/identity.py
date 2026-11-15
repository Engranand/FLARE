"""Identity validation services for condition roles and instruments.

Enforces M3 R5:
Corrected role and instrument descriptions require new identities and new
version-qualified codes, with evidence explicitly locating the correction.
Existing references remain unchanged; no automatic successor selection is allowed.
"""
from collections.abc import Iterable
import re


class IdentityValidationError(ValueError):
    """Raised when an identity code does not satisfy version-qualification rules."""
    pass


# Base code pattern: lowercase alphanumeric and underscores, starting with a letter
BASE_CODE_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")

# Version-qualified code pattern: <base_name>_v<positive_integer>
VERSION_QUALIFIED_PATTERN = re.compile(r"^(?P<base>[a-z][a-z0-9_]*)_v(?P<ver>[0-9]+)$")


def parse_code_version(code: str) -> tuple[str, int | None]:
    """Extract the base code and version suffix if present.

    Returns (base_code, version) where version is None for unversioned base codes.
    """
    match = VERSION_QUALIFIED_PATTERN.match(code)
    if match:
        return match.group("base"), int(match.group("ver"))
    return code, None


def validate_identity_code(
    code: str,
    existing_codes: Iterable[str],
    *,
    entity_name: str = "identity",
) -> None:
    """Validate that a role or instrument code satisfies uniqueness and version qualification.

    Rules:
    1. Code must match valid identifier pattern (lowercase, starts with letter).
    2. Code must not already exist in existing_codes (uniqueness).
    3. If registering a correction for an existing base code, the code must be
       explicitly version-qualified with `_v<N>` where N >= 2 and N is strictly
       greater than any existing version suffix for that base code.
    4. Suffix is autonomous to this identity stream, never tied to condition revision.
    """
    if not code or not BASE_CODE_PATTERN.match(code):
        raise IdentityValidationError(
            f"Invalid {entity_name} code '{code}': must be non-empty, lowercase alphanumeric and underscores, starting with a letter"
        )

    existing_set = set(existing_codes)
    if code in existing_set:
        raise IdentityValidationError(
            f"Duplicate {entity_name} code '{code}': already registered in this investigation"
        )

    base, ver = parse_code_version(code)

    if ver is not None and ver < 2:
        raise IdentityValidationError(
            f"Invalid {entity_name} version suffix '_v{ver}': version-qualified successors must use _v2 or higher"
        )

    # Check if a base code already exists for this stream
    base_exists = base in existing_set or any(parse_code_version(c)[0] == base for c in existing_set)

    if base_exists and ver is None:
        raise IdentityValidationError(
            f"Unversioned code '{code}' cannot correct existing '{base}': corrected definitions require a version-qualified code (e.g. '{base}_v2')"
        )

    if ver is not None and base_exists:
        existing_versions = [
            parse_code_version(c)[1]
            for c in existing_set
            if parse_code_version(c)[0] == base and parse_code_version(c)[1] is not None
        ]
        if existing_versions and ver <= max(existing_versions):
            raise IdentityValidationError(
                f"Version conflict for '{code}': version _v{ver} must be greater than existing _v{max(existing_versions)}"
            )
