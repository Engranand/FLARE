"""Tests for condition role and instrument identity validation services."""
import pytest

from app.services.identity import (
    IdentityValidationError,
    parse_code_version,
    validate_identity_code,
)


def test_parse_code_version():
    assert parse_code_version("air_speed") == ("air_speed", None)
    assert parse_code_version("air_speed_v2") == ("air_speed", 2)
    assert parse_code_version("radiometer_a_v10") == ("radiometer_a", 10)
    assert parse_code_version("material") == ("material", None)


def test_valid_initial_base_registration():
    validate_identity_code("air_speed", [])
    validate_identity_code("radiometer_a", ["air_speed", "material"])
    validate_identity_code("oxygen_sensor", [])


def test_duplicate_code_rejected():
    with pytest.raises(IdentityValidationError, match="Duplicate"):
        validate_identity_code("air_speed", ["air_speed"])

    with pytest.raises(IdentityValidationError, match="Duplicate"):
        validate_identity_code("air_speed_v2", ["air_speed", "air_speed_v2"])


def test_invalid_code_format_rejected():
    with pytest.raises(IdentityValidationError, match="Invalid"):
        validate_identity_code("AirSpeed", [])

    with pytest.raises(IdentityValidationError, match="Invalid"):
        validate_identity_code("123sensor", [])

    with pytest.raises(IdentityValidationError, match="Invalid"):
        validate_identity_code("air speed", [])

    with pytest.raises(IdentityValidationError, match="Invalid"):
        validate_identity_code("", [])


def test_unversioned_correction_rejected():
    # If air_speed exists, an unversioned air_speed is rejected as duplicate
    # And attempting to re-register unversioned code when versioned exists is rejected
    with pytest.raises(IdentityValidationError, match="cannot correct existing"):
        validate_identity_code("air_speed", ["air_speed_v2"])


def test_version_suffix_must_be_v2_or_higher():
    with pytest.raises(IdentityValidationError, match="_v2 or higher"):
        validate_identity_code("air_speed_v1", ["air_speed"])


def test_valid_version_qualified_successors():
    # Successor to air_speed
    validate_identity_code("air_speed_v2", ["air_speed"])
    # Successor to air_speed_v2
    validate_identity_code("air_speed_v3", ["air_speed", "air_speed_v2"])
    # Successor with gap (e.g. v5 when v2 exists)
    validate_identity_code("air_speed_v5", ["air_speed", "air_speed_v2"])


def test_stale_or_lower_version_suffix_rejected():
    with pytest.raises(IdentityValidationError, match="must be greater than"):
        validate_identity_code("air_speed_v2", ["air_speed", "air_speed_v3"])

    with pytest.raises(IdentityValidationError, match="Duplicate"):
        validate_identity_code("air_speed_v3", ["air_speed", "air_speed_v3"])


def test_independent_role_streams():
    # Version numbers on different base codes are completely independent
    existing = ["air_speed", "air_speed_v2", "oxygen", "oxygen_v5"]
    validate_identity_code("air_speed_v3", existing)
    validate_identity_code("oxygen_v6", existing)
    validate_identity_code("radiometer", existing)
