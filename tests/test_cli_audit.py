"""Tests for the audit CLI command."""

from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from typer.testing import CliRunner

from depswiz.cli.app import app
from depswiz.core.models import AuditResult, CheckResult, Package, Severity, Vulnerability

runner = CliRunner()


@pytest.fixture
def mock_packages() -> list[Package]:
    """Create mock packages for testing."""
    return [
        Package(
            name="vulnerable-pkg",
            language="python",
            constraint=">=1.0.0",
            current_version="1.0.0",
            latest_version="1.2.0",
            is_dev=False,
        ),
        Package(
            name="safe-pkg",
            language="python",
            constraint=">=2.0.0",
            current_version="2.0.0",
            latest_version="2.0.0",
            is_dev=False,
        ),
    ]


@pytest.fixture
def mock_vulnerability() -> Vulnerability:
    """Create a mock vulnerability for testing."""
    return Vulnerability(
        id="GHSA-test-1234",
        aliases=["CVE-2024-12345"],
        severity=Severity.HIGH,
        cvss_score=7.5,
        cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N",
        title="Test Vulnerability",
        description="A test vulnerability for testing purposes.",
        affected_versions="< 1.2.0",
        fixed_version="1.2.0",
        source="ghsa",
        references=["https://example.com/advisory"],
        published=datetime(2024, 1, 15),
    )


@pytest.fixture
def mock_audit_result(mock_packages: list[Package], mock_vulnerability: Vulnerability) -> AuditResult:
    """Create a mock audit result with vulnerabilities."""
    return AuditResult(
        packages=mock_packages,
        vulnerabilities=[(mock_packages[0], mock_vulnerability)],
        path=Path("."),
    )


@pytest.fixture
def mock_clean_audit_result(mock_packages: list[Package]) -> AuditResult:
    """Create a mock audit result with no vulnerabilities."""
    return AuditResult(
        packages=mock_packages,
        vulnerabilities=[],
        path=Path("."),
    )


class TestAuditCommand:
    """Tests for the audit command."""

    def test_audit_help(self) -> None:
        """Test audit command help text."""
        result = runner.invoke(app, ["audit", "--help"])
        assert result.exit_code == 0
        # Check for key content - options may be truncated in narrow terminals
        assert "audit" in result.stdout.lower() or "vulnerabilities" in result.stdout.lower()

    @patch("depswiz.cli.commands.audit.audit_packages", new_callable=AsyncMock)
    @patch("depswiz.cli.commands.audit.scan_dependencies", new_callable=AsyncMock)
    def test_audit_with_vulnerabilities(
        self,
        mock_scan: AsyncMock,
        mock_audit: AsyncMock,
        mock_packages: list[Package],
        mock_audit_result: AuditResult,
        tmp_path: Path,
    ) -> None:
        """Test audit command when vulnerabilities are found."""
        mock_scan.return_value = CheckResult(packages=mock_packages, path=tmp_path)
        mock_audit.return_value = mock_audit_result

        result = runner.invoke(app, ["audit", str(tmp_path)])
        # Should fail because high severity vulnerability was found
        assert result.exit_code == 1

    @patch("depswiz.cli.commands.audit.audit_packages", new_callable=AsyncMock)
    @patch("depswiz.cli.commands.audit.scan_dependencies", new_callable=AsyncMock)
    def test_audit_no_vulnerabilities(
        self,
        mock_scan: AsyncMock,
        mock_audit: AsyncMock,
        mock_packages: list[Package],
        mock_clean_audit_result: AuditResult,
        tmp_path: Path,
    ) -> None:
        """Test audit command when no vulnerabilities are found."""
        mock_scan.return_value = CheckResult(packages=mock_packages, path=tmp_path)
        mock_audit.return_value = mock_clean_audit_result

        result = runner.invoke(app, ["audit", str(tmp_path)])
        assert result.exit_code == 0

    @patch("depswiz.cli.commands.audit.audit_packages", new_callable=AsyncMock)
    @patch("depswiz.cli.commands.audit.scan_dependencies", new_callable=AsyncMock)
    def test_audit_json_format(
        self,
        mock_scan: AsyncMock,
        mock_audit: AsyncMock,
        mock_packages: list[Package],
        mock_audit_result: AuditResult,
        tmp_path: Path,
    ) -> None:
        """Test audit command with JSON output format."""
        mock_scan.return_value = CheckResult(packages=mock_packages, path=tmp_path)
        mock_audit.return_value = mock_audit_result

        result = runner.invoke(app, ["audit", "--format", "json", str(tmp_path)])
        # Will still fail due to high severity
        assert result.exit_code == 1
        assert '"vulnerabilities"' in result.stdout
        assert '"GHSA-test-1234"' in result.stdout

    @patch("depswiz.cli.commands.audit.audit_packages", new_callable=AsyncMock)
    @patch("depswiz.cli.commands.audit.scan_dependencies", new_callable=AsyncMock)
    def test_audit_markdown_format(
        self,
        mock_scan: AsyncMock,
        mock_audit: AsyncMock,
        mock_packages: list[Package],
        mock_audit_result: AuditResult,
        tmp_path: Path,
    ) -> None:
        """Test audit command with Markdown output format."""
        mock_scan.return_value = CheckResult(packages=mock_packages, path=tmp_path)
        mock_audit.return_value = mock_audit_result

        result = runner.invoke(app, ["audit", "--format", "markdown", str(tmp_path)])
        assert result.exit_code == 1
        assert "# Security Audit Report" in result.stdout


class TestAuditSeverityFiltering:
    """Tests for audit command severity filtering."""

    @patch("depswiz.cli.commands.audit.audit_packages", new_callable=AsyncMock)
    @patch("depswiz.cli.commands.audit.scan_dependencies", new_callable=AsyncMock)
    def test_audit_filter_by_severity(
        self,
        mock_scan: AsyncMock,
        mock_audit: AsyncMock,
        mock_packages: list[Package],
        tmp_path: Path,
    ) -> None:
        """Test audit command filters by minimum severity."""
        low_vuln = Vulnerability(
            id="GHSA-low-1234",
            aliases=[],
            severity=Severity.LOW,
            title="Low Severity Issue",
            description="A low severity issue.",
            affected_versions="< 2.0.0",
            source="osv",
        )
        audit_result = AuditResult(
            packages=mock_packages,
            vulnerabilities=[(mock_packages[0], low_vuln)],
            path=tmp_path,
        )
        mock_scan.return_value = CheckResult(packages=mock_packages, path=tmp_path)
        mock_audit.return_value = audit_result

        # Filter for high severity only - should not show low
        result = runner.invoke(
            app, ["audit", "--severity", "high", "--format", "json", str(tmp_path)]
        )
        assert result.exit_code == 0  # No high severity vulns to fail on
        assert '"vulnerabilities": []' in result.stdout

    @patch("depswiz.cli.commands.audit.audit_packages", new_callable=AsyncMock)
    @patch("depswiz.cli.commands.audit.scan_dependencies", new_callable=AsyncMock)
    def test_audit_fail_on_critical_only(
        self,
        mock_scan: AsyncMock,
        mock_audit: AsyncMock,
        mock_packages: list[Package],
        mock_audit_result: AuditResult,
        tmp_path: Path,
    ) -> None:
        """Test audit command only fails on critical when --fail-on critical."""
        mock_scan.return_value = CheckResult(packages=mock_packages, path=tmp_path)
        mock_audit.return_value = mock_audit_result

        # --fail-on critical means high severity should not cause failure
        result = runner.invoke(app, ["audit", "--fail-on", "critical", str(tmp_path)])
        assert result.exit_code == 0  # High severity should not fail

    def test_audit_invalid_severity(self, tmp_path: Path) -> None:
        """Test audit command rejects invalid severity."""
        result = runner.invoke(app, ["audit", "--severity", "invalid", str(tmp_path)])
        assert result.exit_code != 0
        # Error message may be in stdout or output (depends on Typer version)
        output = result.stdout + (result.stderr or "")
        assert "Invalid severity" in output or "invalid" in output.lower()


class TestAuditIgnore:
    """Tests for audit command vulnerability ignoring."""

    @patch("depswiz.cli.commands.audit.audit_packages", new_callable=AsyncMock)
    @patch("depswiz.cli.commands.audit.scan_dependencies", new_callable=AsyncMock)
    def test_audit_ignore_specific_id(
        self,
        mock_scan: AsyncMock,
        mock_audit: AsyncMock,
        mock_packages: list[Package],
        mock_audit_result: AuditResult,
        tmp_path: Path,
    ) -> None:
        """Test audit command ignores specific vulnerability IDs."""
        mock_scan.return_value = CheckResult(packages=mock_packages, path=tmp_path)
        mock_audit.return_value = mock_audit_result

        result = runner.invoke(
            app, ["audit", "--ignore", "GHSA-test-1234", str(tmp_path)]
        )
        # Should succeed because the only vulnerability is ignored
        assert result.exit_code == 0

    @patch("depswiz.cli.commands.audit.audit_packages", new_callable=AsyncMock)
    @patch("depswiz.cli.commands.audit.scan_dependencies", new_callable=AsyncMock)
    def test_audit_ignore_file(
        self,
        mock_scan: AsyncMock,
        mock_audit: AsyncMock,
        mock_packages: list[Package],
        mock_audit_result: AuditResult,
        tmp_path: Path,
    ) -> None:
        """Test audit command reads ignore file."""
        mock_scan.return_value = CheckResult(packages=mock_packages, path=tmp_path)
        mock_audit.return_value = mock_audit_result

        # Create ignore file
        ignore_file = tmp_path / ".depswiz-ignore"
        ignore_file.write_text("# Comment\nGHSA-test-1234\n")

        result = runner.invoke(
            app, ["audit", "--ignore-file", str(ignore_file), str(tmp_path)]
        )
        # Should succeed because vulnerability is in ignore file
        assert result.exit_code == 0


class TestAuditOutputFile:
    """Tests for audit command output file option."""

    @patch("depswiz.cli.commands.audit.audit_packages", new_callable=AsyncMock)
    @patch("depswiz.cli.commands.audit.scan_dependencies", new_callable=AsyncMock)
    def test_audit_output_to_file(
        self,
        mock_scan: AsyncMock,
        mock_audit: AsyncMock,
        mock_packages: list[Package],
        mock_clean_audit_result: AuditResult,
        tmp_path: Path,
    ) -> None:
        """Test audit command writes output to file."""
        mock_scan.return_value = CheckResult(packages=mock_packages, path=tmp_path)
        mock_audit.return_value = mock_clean_audit_result
        output_file = tmp_path / "audit-report.json"

        result = runner.invoke(
            app, ["audit", "--format", "json", "--output", str(output_file), str(tmp_path)]
        )
        assert result.exit_code == 0
        assert output_file.exists()
        content = output_file.read_text()
        assert '"vulnerabilities"' in content
