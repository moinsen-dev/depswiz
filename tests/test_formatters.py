"""Tests for output formatters."""

import json
from datetime import datetime
from pathlib import Path

import pytest
from rich.console import Console

from depswiz.cli.formatters import (
    CliFormatter,
    HtmlFormatter,
    JsonFormatter,
    MarkdownFormatter,
)
from depswiz.core.models import (
    AuditResult,
    CheckResult,
    LicenseCategory,
    LicenseInfo,
    LicenseResult,
    Package,
    Severity,
    UpdateType,
    Vulnerability,
)


@pytest.fixture
def sample_packages() -> list[Package]:
    """Create sample packages for testing."""
    return [
        Package(
            name="requests",
            language="python",
            constraint=">=2.28.0",
            current_version="2.28.0",
            latest_version="2.31.0",
            update_type=UpdateType.MINOR,
            is_dev=False,
        ),
        Package(
            name="pytest",
            language="python",
            constraint=">=8.0.0",
            current_version="8.0.0",
            latest_version="8.0.0",
            update_type=None,
            is_dev=True,
        ),
        Package(
            name="httpx",
            language="python",
            constraint=">=0.25.0",
            current_version="0.25.0",
            latest_version="0.27.0",
            update_type=UpdateType.MINOR,
            is_dev=False,
        ),
    ]


@pytest.fixture
def sample_check_result(sample_packages: list[Package]) -> CheckResult:
    """Create a sample check result."""
    return CheckResult(
        packages=sample_packages,
        path=Path("/test/project"),
    )


@pytest.fixture
def sample_vulnerability() -> Vulnerability:
    """Create a sample vulnerability."""
    return Vulnerability(
        id="GHSA-test-1234",
        aliases=["CVE-2024-12345"],
        severity=Severity.HIGH,
        cvss_score=7.5,
        cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N",
        title="Test Vulnerability",
        description="A test vulnerability for testing purposes.",
        affected_versions="< 2.31.0",
        fixed_version="2.31.0",
        source="ghsa",
        references=["https://example.com/advisory"],
        published=datetime(2024, 1, 15),
    )


@pytest.fixture
def sample_audit_result(
    sample_packages: list[Package], sample_vulnerability: Vulnerability
) -> AuditResult:
    """Create a sample audit result."""
    return AuditResult(
        packages=sample_packages,
        vulnerabilities=[(sample_packages[0], sample_vulnerability)],
        path=Path("/test/project"),
    )


@pytest.fixture
def sample_packages_with_licenses() -> list[Package]:
    """Create sample packages with license info."""
    return [
        Package(
            name="requests",
            language="python",
            current_version="2.31.0",
            license_info=LicenseInfo(
                spdx_id="Apache-2.0",
                name="Apache License 2.0",
                category=LicenseCategory.PERMISSIVE,
                is_copyleft=False,
            ),
        ),
        Package(
            name="gpl-pkg",
            language="python",
            current_version="1.0.0",
            license_info=LicenseInfo(
                spdx_id="GPL-3.0",
                name="GNU General Public License v3.0",
                category=LicenseCategory.STRONG_COPYLEFT,
                is_copyleft=True,
            ),
        ),
    ]


@pytest.fixture
def sample_license_result(sample_packages_with_licenses: list[Package]) -> LicenseResult:
    """Create a sample license result."""
    return LicenseResult(
        packages=sample_packages_with_licenses,
        violations=[(sample_packages_with_licenses[1], "GPL-3.0 is not allowed")],
        warnings=[],
        path=Path("/test/project"),
    )


class TestJsonFormatter:
    """Tests for JSON formatter."""

    def test_format_check_result(self, sample_check_result: CheckResult) -> None:
        """Test formatting check result as JSON."""
        formatter = JsonFormatter()
        output = formatter.format_check_result(sample_check_result)

        data = json.loads(output)
        assert data["command"] == "check"
        assert data["status"] == "outdated"
        assert data["summary"]["total_packages"] == 3
        assert data["summary"]["outdated_packages"] == 2
        assert len(data["packages"]) == 3

    def test_format_check_result_all_up_to_date(self) -> None:
        """Test formatting check result when all packages are up to date."""
        packages = [
            Package(
                name="pkg",
                language="python",
                current_version="1.0.0",
                latest_version="1.0.0",
                update_type=None,
            ),
        ]
        result = CheckResult(packages=packages, path=Path("."))

        formatter = JsonFormatter()
        output = formatter.format_check_result(result)

        data = json.loads(output)
        assert data["status"] == "up_to_date"
        assert data["summary"]["outdated_packages"] == 0

    def test_format_audit_result(self, sample_audit_result: AuditResult) -> None:
        """Test formatting audit result as JSON."""
        formatter = JsonFormatter()
        output = formatter.format_audit_result(sample_audit_result)

        data = json.loads(output)
        assert data["command"] == "audit"
        assert data["status"] == "vulnerable"
        assert data["summary"]["total_vulnerabilities"] == 1
        assert data["summary"]["by_severity"]["high"] == 1
        assert len(data["vulnerabilities"]) == 1
        assert data["vulnerabilities"][0]["vulnerability"]["id"] == "GHSA-test-1234"

    def test_format_audit_result_clean(self, sample_packages: list[Package]) -> None:
        """Test formatting audit result when no vulnerabilities found."""
        result = AuditResult(packages=sample_packages, vulnerabilities=[], path=Path("."))

        formatter = JsonFormatter()
        output = formatter.format_audit_result(result)

        data = json.loads(output)
        assert data["status"] == "clean"
        assert data["summary"]["total_vulnerabilities"] == 0

    def test_format_license_result(self, sample_license_result: LicenseResult) -> None:
        """Test formatting license result as JSON."""
        formatter = JsonFormatter()
        output = formatter.format_license_result(sample_license_result)

        data = json.loads(output)
        assert data["command"] == "licenses"
        assert data["status"] == "violation"
        assert len(data["violations"]) == 1
        assert "GPL-3.0" in data["violations"][0]["reason"]


class TestMarkdownFormatter:
    """Tests for Markdown formatter."""

    def test_format_check_result(self, sample_check_result: CheckResult) -> None:
        """Test formatting check result as Markdown."""
        formatter = MarkdownFormatter()
        output = formatter.format_check_result(sample_check_result)

        assert "# Dependency Report" in output
        assert "## Summary" in output
        assert "| Total Packages | 3 |" in output
        assert "| Outdated | 2 |" in output
        assert "## Outdated Packages" in output
        assert "requests" in output

    def test_format_check_result_no_outdated(self) -> None:
        """Test formatting check result when nothing is outdated."""
        packages = [
            Package(
                name="pkg",
                language="python",
                current_version="1.0.0",
                latest_version="1.0.0",
            ),
        ]
        result = CheckResult(packages=packages, path=Path("."))

        formatter = MarkdownFormatter()
        output = formatter.format_check_result(result)

        assert "# Dependency Report" in output
        assert "## Outdated Packages" not in output

    def test_format_audit_result(self, sample_audit_result: AuditResult) -> None:
        """Test formatting audit result as Markdown."""
        formatter = MarkdownFormatter()
        output = formatter.format_audit_result(sample_audit_result)

        assert "# Security Audit Report" in output
        assert "## Summary" in output
        assert "1 vulnerabilities found" in output
        assert "GHSA-test-1234" in output
        assert "Severity" in output
        assert "High" in output

    def test_format_audit_result_no_vulns(self, sample_packages: list[Package]) -> None:
        """Test formatting audit result when no vulnerabilities."""
        result = AuditResult(packages=sample_packages, vulnerabilities=[], path=Path("."))

        formatter = MarkdownFormatter()
        output = formatter.format_audit_result(result)

        assert "# Security Audit Report" in output
        assert "No vulnerabilities found" in output

    def test_format_audit_result_with_fix(self, sample_audit_result: AuditResult) -> None:
        """Test formatting audit result with fix recommendations."""
        formatter = MarkdownFormatter()
        output = formatter.format_audit_result(sample_audit_result, show_fix=True)

        assert "## Recommendations" in output
        assert "requests" in output
        assert "2.31.0" in output

    def test_format_license_result(self, sample_license_result: LicenseResult) -> None:
        """Test formatting license result as Markdown."""
        formatter = MarkdownFormatter()
        output = formatter.format_license_result(sample_license_result)

        assert "# License Compliance Report" in output
        assert "## Summary" in output
        assert "## Violations" in output
        assert "gpl-pkg" in output

    def test_severity_badge(self) -> None:
        """Test severity badge generation."""
        formatter = MarkdownFormatter()

        critical = formatter._severity_badge("critical")
        assert "critical" in critical.lower()

        high = formatter._severity_badge("high")
        assert "high" in high.lower()


class TestHtmlFormatter:
    """Tests for HTML formatter."""

    def test_format_check_result(self, sample_check_result: CheckResult) -> None:
        """Test formatting check result as HTML."""
        formatter = HtmlFormatter()
        output = formatter.format_check_result(sample_check_result)

        assert "<html" in output
        assert "Dependency Check Report" in output
        assert "requests" in output

    def test_format_audit_result(self, sample_audit_result: AuditResult) -> None:
        """Test formatting audit result as HTML."""
        formatter = HtmlFormatter()
        output = formatter.format_audit_result(sample_audit_result)

        assert "<html" in output
        assert "Security Audit" in output
        assert "GHSA-test-1234" in output

    def test_format_license_result(self, sample_license_result: LicenseResult) -> None:
        """Test formatting license result as HTML."""
        formatter = HtmlFormatter()
        output = formatter.format_license_result(sample_license_result)

        assert "<html" in output
        assert "License" in output


class TestCliFormatter:
    """Tests for CLI (Rich) formatter."""

    def test_format_check_result(self, sample_check_result: CheckResult) -> None:
        """Test formatting check result for CLI."""
        console = Console(record=True, force_terminal=True)
        formatter = CliFormatter(console)
        output = formatter.format_check_result(sample_check_result)

        # CLI formatter prints directly, output is empty string
        assert output == ""

    def test_format_audit_result(self, sample_audit_result: AuditResult) -> None:
        """Test formatting audit result for CLI."""
        console = Console(record=True, force_terminal=True)
        formatter = CliFormatter(console)
        output = formatter.format_audit_result(sample_audit_result)

        # CLI formatter prints directly
        assert output == ""

    def test_format_license_result(self, sample_license_result: LicenseResult) -> None:
        """Test formatting license result for CLI."""
        console = Console(record=True, force_terminal=True)
        formatter = CliFormatter(console)
        output = formatter.format_license_result(sample_license_result)

        # CLI formatter prints directly
        assert output == ""


class TestCheckResultProperties:
    """Tests for CheckResult computed properties."""

    def test_outdated_packages(self, sample_check_result: CheckResult) -> None:
        """Test outdated_packages property."""
        outdated = sample_check_result.outdated_packages
        assert len(outdated) == 2
        assert all(pkg.is_outdated for pkg in outdated)

    def test_up_to_date_packages(self, sample_check_result: CheckResult) -> None:
        """Test up_to_date_packages property."""
        up_to_date = sample_check_result.up_to_date_packages
        assert len(up_to_date) == 1
        assert all(not pkg.is_outdated for pkg in up_to_date)

    def test_total_packages(self, sample_check_result: CheckResult) -> None:
        """Test total_packages property."""
        assert sample_check_result.total_packages == 3

    def test_update_breakdown(self, sample_check_result: CheckResult) -> None:
        """Test update_breakdown property."""
        breakdown = sample_check_result.update_breakdown
        assert breakdown[UpdateType.MINOR] == 2
        assert breakdown[UpdateType.MAJOR] == 0
        assert breakdown[UpdateType.PATCH] == 0


class TestAuditResultProperties:
    """Tests for AuditResult computed properties."""

    def test_total_vulnerabilities(self, sample_audit_result: AuditResult) -> None:
        """Test total_vulnerabilities property."""
        assert sample_audit_result.total_vulnerabilities == 1

    def test_severity_counts(self, sample_audit_result: AuditResult) -> None:
        """Test severity count properties."""
        assert sample_audit_result.high_count == 1
        assert sample_audit_result.critical_count == 0
        assert sample_audit_result.medium_count == 0
        assert sample_audit_result.low_count == 0


class TestLicenseResultProperties:
    """Tests for LicenseResult computed properties."""

    def test_has_violations(self, sample_license_result: LicenseResult) -> None:
        """Test has_violations property."""
        assert sample_license_result.has_violations is True

    def test_license_summary(self, sample_license_result: LicenseResult) -> None:
        """Test license_summary property."""
        summary = sample_license_result.license_summary
        assert "Apache-2.0" in summary
        assert "GPL-3.0" in summary
