"""Tests for deprecations module."""

from datetime import datetime
from pathlib import Path

import pytest

from depswiz.deprecations.models import (
    Deprecation,
    DeprecationResult,
    DeprecationStatus,
)


class TestDeprecationStatus:
    """Tests for DeprecationStatus enum."""

    def test_from_analyzer_severity_error(self) -> None:
        """Test ERROR maps to BREAKING_SOON."""
        assert DeprecationStatus.from_analyzer_severity("ERROR") == DeprecationStatus.BREAKING_SOON

    def test_from_analyzer_severity_warning(self) -> None:
        """Test WARNING maps to DEPRECATED."""
        assert DeprecationStatus.from_analyzer_severity("WARNING") == DeprecationStatus.DEPRECATED

    def test_from_analyzer_severity_info(self) -> None:
        """Test INFO maps to INFO."""
        assert DeprecationStatus.from_analyzer_severity("INFO") == DeprecationStatus.INFO

    def test_from_analyzer_severity_case_insensitive(self) -> None:
        """Test severity mapping is case insensitive."""
        assert DeprecationStatus.from_analyzer_severity("warning") == DeprecationStatus.DEPRECATED
        assert DeprecationStatus.from_analyzer_severity("Warning") == DeprecationStatus.DEPRECATED

    def test_from_analyzer_severity_unknown(self) -> None:
        """Test unknown severity defaults to DEPRECATED."""
        assert DeprecationStatus.from_analyzer_severity("UNKNOWN") == DeprecationStatus.DEPRECATED

    def test_status_comparison_lt(self) -> None:
        """Test status less-than comparison."""
        assert DeprecationStatus.INFO < DeprecationStatus.DEPRECATED
        assert DeprecationStatus.DEPRECATED < DeprecationStatus.REMOVAL_PLANNED
        assert DeprecationStatus.REMOVAL_PLANNED < DeprecationStatus.BREAKING_SOON

    def test_status_comparison_le(self) -> None:
        """Test status less-than-or-equal comparison."""
        assert DeprecationStatus.INFO <= DeprecationStatus.INFO
        assert DeprecationStatus.INFO <= DeprecationStatus.DEPRECATED
        assert DeprecationStatus.DEPRECATED <= DeprecationStatus.BREAKING_SOON

    def test_status_comparison_not_implemented(self) -> None:
        """Test comparison with non-status returns NotImplemented."""
        result = DeprecationStatus.INFO.__lt__("other")
        assert result is NotImplemented

    def test_status_values(self) -> None:
        """Test status enum values."""
        assert DeprecationStatus.DEPRECATED.value == "deprecated"
        assert DeprecationStatus.REMOVAL_PLANNED.value == "removal"
        assert DeprecationStatus.BREAKING_SOON.value == "breaking"
        assert DeprecationStatus.INFO.value == "info"


class TestDeprecation:
    """Tests for Deprecation dataclass."""

    @pytest.fixture
    def sample_deprecation(self) -> Deprecation:
        """Create a sample deprecation for testing."""
        return Deprecation(
            rule_id="deprecated_member_use",
            message="'FlatButton' is deprecated and shouldn't be used. Use TextButton instead.",
            file_path=Path("/project/lib/widgets/button.dart"),
            line=42,
            column=12,
            status=DeprecationStatus.DEPRECATED,
            package="flutter",
            replacement="TextButton",
            fix_available=True,
        )

    def test_location_property(self, sample_deprecation: Deprecation) -> None:
        """Test location property returns full path."""
        assert sample_deprecation.location == "/project/lib/widgets/button.dart:42:12"

    def test_short_location_property(self, sample_deprecation: Deprecation) -> None:
        """Test short_location property returns filename:line."""
        assert sample_deprecation.short_location == "button.dart:42"

    def test_deprecation_defaults(self) -> None:
        """Test deprecation default values."""
        dep = Deprecation(
            rule_id="test_rule",
            message="Test message",
            file_path=Path("/test.dart"),
            line=1,
            column=1,
        )
        assert dep.status == DeprecationStatus.DEPRECATED
        assert dep.package is None
        assert dep.replacement is None
        assert dep.fix_available is False
        assert dep.references == []


class TestDeprecationResult:
    """Tests for DeprecationResult dataclass."""

    @pytest.fixture
    def empty_result(self) -> DeprecationResult:
        """Create an empty deprecation result."""
        return DeprecationResult(path=Path("/project"))

    @pytest.fixture
    def sample_result(self) -> DeprecationResult:
        """Create a sample deprecation result with data."""
        deprecations = [
            Deprecation(
                rule_id="deprecated_member_use",
                message="FlatButton is deprecated",
                file_path=Path("/project/lib/a.dart"),
                line=10,
                column=5,
                status=DeprecationStatus.DEPRECATED,
                package="flutter",
                fix_available=True,
            ),
            Deprecation(
                rule_id="deprecated_member_use",
                message="RaisedButton is deprecated",
                file_path=Path("/project/lib/a.dart"),
                line=20,
                column=5,
                status=DeprecationStatus.DEPRECATED,
                package="flutter",
                fix_available=True,
            ),
            Deprecation(
                rule_id="deprecated_member_use",
                message="MaterialState is deprecated",
                file_path=Path("/project/lib/b.dart"),
                line=15,
                column=3,
                status=DeprecationStatus.REMOVAL_PLANNED,
                package="flutter",
                fix_available=False,
            ),
            Deprecation(
                rule_id="deprecated_member_use_from_same_package",
                message="Internal API deprecated",
                file_path=Path("/project/lib/c.dart"),
                line=5,
                column=1,
                status=DeprecationStatus.BREAKING_SOON,
                package="my_app",
                fix_available=False,
            ),
        ]
        return DeprecationResult(
            path=Path("/project"),
            deprecations=deprecations,
            dart_version="3.2.0",
            flutter_version="3.16.0",
            fixable_count=2,
        )

    def test_total_count_empty(self, empty_result: DeprecationResult) -> None:
        """Test total_count with no deprecations."""
        assert empty_result.total_count == 0

    def test_total_count(self, sample_result: DeprecationResult) -> None:
        """Test total_count with deprecations."""
        assert sample_result.total_count == 4

    def test_by_status_empty(self, empty_result: DeprecationResult) -> None:
        """Test by_status with no deprecations."""
        assert empty_result.by_status == {}

    def test_by_status(self, sample_result: DeprecationResult) -> None:
        """Test by_status grouping."""
        by_status = sample_result.by_status
        assert by_status[DeprecationStatus.DEPRECATED] == 2
        assert by_status[DeprecationStatus.REMOVAL_PLANNED] == 1
        assert by_status[DeprecationStatus.BREAKING_SOON] == 1

    def test_by_package_empty(self, empty_result: DeprecationResult) -> None:
        """Test by_package with no deprecations."""
        assert empty_result.by_package == {}

    def test_by_package(self, sample_result: DeprecationResult) -> None:
        """Test by_package grouping."""
        by_package = sample_result.by_package
        assert by_package["flutter"] == 3
        assert by_package["my_app"] == 1

    def test_by_rule_empty(self, empty_result: DeprecationResult) -> None:
        """Test by_rule with no deprecations."""
        assert empty_result.by_rule == {}

    def test_by_rule(self, sample_result: DeprecationResult) -> None:
        """Test by_rule grouping."""
        by_rule = sample_result.by_rule
        assert by_rule["deprecated_member_use"] == 3
        assert by_rule["deprecated_member_use_from_same_package"] == 1

    def test_by_file_empty(self, empty_result: DeprecationResult) -> None:
        """Test by_file with no deprecations."""
        assert empty_result.by_file == {}

    def test_by_file(self, sample_result: DeprecationResult) -> None:
        """Test by_file grouping."""
        by_file = sample_result.by_file
        assert len(by_file[Path("/project/lib/a.dart")]) == 2
        assert len(by_file[Path("/project/lib/b.dart")]) == 1
        assert len(by_file[Path("/project/lib/c.dart")]) == 1

    def test_breaking_count_empty(self, empty_result: DeprecationResult) -> None:
        """Test breaking_count with no deprecations."""
        assert empty_result.breaking_count == 0

    def test_breaking_count(self, sample_result: DeprecationResult) -> None:
        """Test breaking_count with deprecations."""
        # 1 REMOVAL_PLANNED + 1 BREAKING_SOON
        assert sample_result.breaking_count == 2

    def test_filter_by_status(self, sample_result: DeprecationResult) -> None:
        """Test filter_by_status method."""
        # Filter for REMOVAL_PLANNED and above
        filtered = sample_result.filter_by_status(DeprecationStatus.REMOVAL_PLANNED)
        assert len(filtered) == 2
        for dep in filtered:
            assert dep.status in (DeprecationStatus.REMOVAL_PLANNED, DeprecationStatus.BREAKING_SOON)

    def test_filter_by_status_breaking(self, sample_result: DeprecationResult) -> None:
        """Test filter_by_status for breaking only."""
        filtered = sample_result.filter_by_status(DeprecationStatus.BREAKING_SOON)
        assert len(filtered) == 1
        assert filtered[0].status == DeprecationStatus.BREAKING_SOON

    def test_filter_fixable_empty(self, empty_result: DeprecationResult) -> None:
        """Test filter_fixable with no deprecations."""
        assert empty_result.filter_fixable() == []

    def test_filter_fixable(self, sample_result: DeprecationResult) -> None:
        """Test filter_fixable method."""
        fixable = sample_result.filter_fixable()
        assert len(fixable) == 2
        for dep in fixable:
            assert dep.fix_available is True

    def test_result_defaults(self) -> None:
        """Test result default values."""
        result = DeprecationResult(path=Path("/test"))
        assert result.deprecations == []
        assert result.dart_version is None
        assert result.flutter_version is None
        assert result.fixable_count == 0
        assert isinstance(result.timestamp, datetime)

    def test_by_package_unknown(self) -> None:
        """Test by_package with None package."""
        result = DeprecationResult(
            path=Path("/test"),
            deprecations=[
                Deprecation(
                    rule_id="test",
                    message="test",
                    file_path=Path("/test.dart"),
                    line=1,
                    column=1,
                    package=None,
                )
            ],
        )
        assert result.by_package == {"unknown": 1}
