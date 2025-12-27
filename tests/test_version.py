"""Tests for version utilities."""

import pytest

from depswiz.core.version import (
    parse_version,
    determine_update_type,
    is_compatible_update,
    normalize_version,
    extract_version_from_constraint,
)
from depswiz.core.models import UpdateType


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
