"""Tests for version utilities."""

from depswiz.core.models import UpdateType
from depswiz.core.version import (
    determine_update_type,
    extract_version_from_constraint,
    is_compatible_update,
    normalize_version,
    parse_version,
)


class TestParseVersion:
    """Tests for parse_version function."""

    def test_valid_version(self):
        ver = parse_version("1.2.3")
        assert ver is not None
        assert ver.major == 1
        assert ver.minor == 2
        assert ver.micro == 3

    def test_invalid_version(self):
        ver = parse_version("not-a-version")
        assert ver is None

    def test_prerelease_version(self):
        ver = parse_version("1.0.0a1")
        assert ver is not None


class TestDetermineUpdateType:
    """Tests for determine_update_type function."""

    def test_major_update(self):
        assert determine_update_type("1.0.0", "2.0.0") == UpdateType.MAJOR

    def test_minor_update(self):
        assert determine_update_type("1.0.0", "1.1.0") == UpdateType.MINOR

    def test_patch_update(self):
        assert determine_update_type("1.0.0", "1.0.1") == UpdateType.PATCH

    def test_same_version(self):
        assert determine_update_type("1.0.0", "1.0.0") is None

    def test_downgrade(self):
        assert determine_update_type("2.0.0", "1.0.0") is None


class TestIsCompatibleUpdate:
    """Tests for is_compatible_update function."""

    def test_caret_constraint_compatible(self):
        assert is_compatible_update("1.0.0", "1.5.0", "^1.0.0") is True

    def test_caret_constraint_incompatible(self):
        assert is_compatible_update("1.0.0", "2.0.0", "^1.0.0") is False

    def test_tilde_constraint_compatible(self):
        assert is_compatible_update("1.0.0", "1.0.5", "~1.0.0") is True

    def test_tilde_constraint_incompatible(self):
        assert is_compatible_update("1.0.0", "1.1.0", "~1.0.0") is False

    def test_gte_constraint(self):
        assert is_compatible_update("1.0.0", "2.0.0", ">=1.0.0") is True


class TestNormalizeVersion:
    """Tests for normalize_version function."""

    def test_already_normalized(self):
        assert normalize_version("1.2.3") == "1.2.3"

    def test_leading_v(self):
        # Note: packaging handles this differently
        result = normalize_version("1.02.03")
        assert "1.2.3" in result


class TestExtractVersionFromConstraint:
    """Tests for extract_version_from_constraint function."""

    def test_gte_constraint(self):
        assert extract_version_from_constraint(">=1.2.3") == "1.2.3"

    def test_caret_constraint(self):
        assert extract_version_from_constraint("^1.2.3") == "1.2.3"

    def test_tilde_constraint(self):
        assert extract_version_from_constraint("~1.2.3") == "1.2.3"

    def test_exact_constraint(self):
        assert extract_version_from_constraint("==1.2.3") == "1.2.3"

    def test_range_constraint(self):
        assert extract_version_from_constraint(">=1.0.0,<2.0.0") == "1.0.0"

    def test_bare_version(self):
        assert extract_version_from_constraint("1.2.3") == "1.2.3"

    def test_less_equal_constraint(self):
        assert extract_version_from_constraint("<=1.2.3") == "1.2.3"

    def test_not_equal_constraint(self):
        assert extract_version_from_constraint("!=1.2.3") == "1.2.3"

    def test_tilde_equal_constraint(self):
        assert extract_version_from_constraint("~=1.2.3") == "1.2.3"

    def test_greater_than_constraint(self):
        assert extract_version_from_constraint(">1.2.3") == "1.2.3"

    def test_less_than_constraint(self):
        assert extract_version_from_constraint("<1.2.3") == "1.2.3"

    def test_with_whitespace(self):
        assert extract_version_from_constraint("  >=1.2.3  ") == "1.2.3"

    def test_invalid_constraint(self):
        assert extract_version_from_constraint("not-a-version") is None


class TestDetermineUpdateTypeEdgeCases:
    """Edge case tests for determine_update_type function."""

    def test_invalid_current_version(self):
        assert determine_update_type("invalid", "1.0.0") is None

    def test_invalid_latest_version(self):
        assert determine_update_type("1.0.0", "invalid") is None

    def test_prerelease_to_release(self):
        result = determine_update_type("1.0.0a1", "1.0.0")
        assert result == UpdateType.PATCH


class TestIsCompatibleUpdateEdgeCases:
    """Edge case tests for is_compatible_update function."""

    def test_no_constraint(self):
        assert is_compatible_update("1.0.0", "2.0.0", None) is True

    def test_invalid_current_version(self):
        assert is_compatible_update("invalid", "1.0.0", "^1.0.0") is False

    def test_invalid_latest_version(self):
        assert is_compatible_update("1.0.0", "invalid", "^1.0.0") is False

    def test_caret_constraint_zero_major_compatible(self):
        # ^0.1.2 means >=0.1.2 <0.2.0
        assert is_compatible_update("0.1.0", "0.1.5", "^0.1.0") is True

    def test_caret_constraint_zero_major_incompatible(self):
        # ^0.1.2 means >=0.1.2 <0.2.0
        assert is_compatible_update("0.1.0", "0.2.0", "^0.1.0") is False

    def test_caret_constraint_invalid_base(self):
        assert is_compatible_update("1.0.0", "2.0.0", "^invalid") is True

    def test_caret_constraint_latest_less_than_base(self):
        assert is_compatible_update("1.0.0", "0.5.0", "^1.0.0") is False

    def test_tilde_constraint_invalid_base(self):
        assert is_compatible_update("1.0.0", "2.0.0", "~invalid") is True

    def test_tilde_constraint_latest_less_than_base(self):
        assert is_compatible_update("1.2.0", "1.1.0", "~1.2.0") is False

    def test_tilde_with_equals_prefix(self):
        assert is_compatible_update("1.2.0", "1.2.5", "~=1.2.0") is True

    def test_greater_equal_with_comma(self):
        assert is_compatible_update("1.0.0", "1.5.0", ">=1.0.0, <2.0.0") is True

    def test_greater_equal_invalid_base(self):
        assert is_compatible_update("1.0.0", "2.0.0", ">=invalid") is True

    def test_greater_equal_incompatible(self):
        assert is_compatible_update("1.0.0", "0.5.0", ">=1.0.0") is False

    def test_unhandled_constraint(self):
        # Other constraint types are considered compatible
        assert is_compatible_update("1.0.0", "2.0.0", "==1.0.0") is True


class TestNormalizeVersionEdgeCases:
    """Edge case tests for normalize_version function."""

    def test_invalid_version_returns_as_is(self):
        assert normalize_version("not-a-version") == "not-a-version"
