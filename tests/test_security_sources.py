"""Tests for vulnerability data sources."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from depswiz.core.models import Package, Severity
from depswiz.security.sources.ghsa import GhsaSource
from depswiz.security.sources.osv import OsvSource
from depswiz.security.sources.rustsec import RustSecSource


class TestOsvSource:
    """Tests for OSV vulnerability source."""

    @pytest.fixture
    def osv_source(self) -> OsvSource:
        """Create an OSV source instance."""
        return OsvSource()

    @pytest.fixture
    def sample_package(self) -> Package:
        """Create a sample package for testing."""
        return Package(
            name="requests",
            language="python",
            current_version="2.28.0",
        )

    def test_source_name(self, osv_source: OsvSource) -> None:
        """Test source name property."""
        assert osv_source.name == "osv"
        assert osv_source.display_name == "Open Source Vulnerabilities (OSV)"

    @pytest.mark.asyncio
    async def test_check_package_no_language(self, osv_source: OsvSource) -> None:
        """Test check_package returns empty for unknown language."""
        pkg = Package(name="test", language=None, current_version="1.0.0")
        client = AsyncMock()
        result = await osv_source.check_package(client, pkg)
        assert result == []

    @pytest.mark.asyncio
    async def test_check_package_no_version(self, osv_source: OsvSource) -> None:
        """Test check_package returns empty when no version."""
        pkg = Package(name="test", language="python", current_version=None)
        client = AsyncMock()
        result = await osv_source.check_package(client, pkg)
        assert result == []

    @pytest.mark.asyncio
    async def test_check_package_with_vulnerability(
        self, osv_source: OsvSource, sample_package: Package
    ) -> None:
        """Test check_package parses vulnerability data correctly."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "vulns": [
                {
                    "id": "PYSEC-2023-1234",
                    "aliases": ["CVE-2023-12345"],
                    "summary": "Test vulnerability",
                    "details": "A test vulnerability description.",
                    "severity": [
                        {
                            "type": "CVSS_V3",
                            "score": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N",
                        }
                    ],
                    "affected": [
                        {
                            "ranges": [{"type": "ECOSYSTEM", "events": [{"fixed": "2.31.0"}]}],
                        }
                    ],
                    "references": [{"url": "https://example.com"}],
                    "published": "2023-01-15T00:00:00Z",
                    "modified": "2023-01-20T00:00:00Z",
                }
            ]
        }

        client = AsyncMock()
        client.post.return_value = mock_response

        result = await osv_source.check_package(client, sample_package)

        assert len(result) == 1
        vuln = result[0]
        assert vuln.id == "PYSEC-2023-1234"
        assert "CVE-2023-12345" in vuln.aliases
        assert vuln.fixed_version == "2.31.0"
        assert vuln.source == "osv"

    @pytest.mark.asyncio
    async def test_check_package_no_vulnerabilities(
        self, osv_source: OsvSource, sample_package: Package
    ) -> None:
        """Test check_package with no vulnerabilities found."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"vulns": []}

        client = AsyncMock()
        client.post.return_value = mock_response

        result = await osv_source.check_package(client, sample_package)
        assert result == []

    @pytest.mark.asyncio
    async def test_check_package_http_error(
        self, osv_source: OsvSource, sample_package: Package
    ) -> None:
        """Test check_package handles HTTP errors gracefully."""
        client = AsyncMock()
        client.post.side_effect = httpx.HTTPStatusError(
            "Server Error", request=MagicMock(), response=MagicMock()
        )

        result = await osv_source.check_package(client, sample_package)
        assert result == []

    @pytest.mark.asyncio
    async def test_check_package_connection_error(
        self, osv_source: OsvSource, sample_package: Package
    ) -> None:
        """Test check_package handles connection errors gracefully."""
        client = AsyncMock()
        client.post.side_effect = httpx.RequestError("Connection failed")

        result = await osv_source.check_package(client, sample_package)
        assert result == []

    def test_parse_severity_from_cvss(self, osv_source: OsvSource) -> None:
        """Test severity parsing from CVSS score."""
        # High severity (7.0-8.9)
        assert Severity.from_cvss(7.5) == Severity.HIGH
        # Critical severity (9.0-10.0)
        assert Severity.from_cvss(9.5) == Severity.CRITICAL
        # Medium severity (4.0-6.9)
        assert Severity.from_cvss(5.5) == Severity.MEDIUM
        # Low severity (0.1-3.9)
        assert Severity.from_cvss(2.5) == Severity.LOW


class TestGhsaSource:
    """Tests for GitHub Security Advisories source."""

    @pytest.fixture
    def ghsa_source(self) -> GhsaSource:
        """Create a GHSA source instance."""
        return GhsaSource()

    @pytest.fixture
    def sample_package(self) -> Package:
        """Create a sample package for testing."""
        return Package(
            name="requests",
            language="python",
            current_version="2.28.0",
        )

    def test_source_name(self, ghsa_source: GhsaSource) -> None:
        """Test source name property."""
        assert ghsa_source.name == "ghsa"
        assert ghsa_source.display_name == "GitHub Security Advisories"

    @pytest.mark.asyncio
    async def test_check_package_no_token(
        self, ghsa_source: GhsaSource, sample_package: Package
    ) -> None:
        """Test check_package returns empty when no GitHub token."""
        with patch.dict("os.environ", {}, clear=True):
            client = AsyncMock()
            result = await ghsa_source.check_package(client, sample_package)
            assert result == []

    @pytest.mark.asyncio
    async def test_check_package_no_language(self, ghsa_source: GhsaSource) -> None:
        """Test check_package returns empty for unknown language."""
        pkg = Package(name="test", language=None, current_version="1.0.0")
        client = AsyncMock()
        result = await ghsa_source.check_package(client, pkg)
        assert result == []

    @pytest.mark.asyncio
    async def test_check_package_with_vulnerability(
        self, ghsa_source: GhsaSource, sample_package: Package
    ) -> None:
        """Test check_package parses GHSA data correctly."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "securityVulnerabilities": {
                    "nodes": [
                        {
                            "advisory": {
                                "ghsaId": "GHSA-abcd-1234",
                                "summary": "Test vulnerability",
                                "description": "A test vulnerability.",
                                "severity": "HIGH",
                                "cvss": {"score": 7.5, "vectorString": "CVSS:3.1/AV:N"},
                                "publishedAt": "2023-01-15T00:00:00Z",
                                "updatedAt": "2023-01-20T00:00:00Z",
                                "references": [{"url": "https://example.com"}],
                                "cwes": {"nodes": [{"cweId": "CWE-79"}]},
                                "identifiers": [{"type": "CVE", "value": "CVE-2023-1234"}],
                            },
                            "vulnerableVersionRange": "< 2.31.0",
                            "firstPatchedVersion": {"identifier": "2.31.0"},
                        }
                    ]
                }
            }
        }

        with patch.dict("os.environ", {"GITHUB_TOKEN": "test-token"}):
            client = AsyncMock()
            client.post.return_value = mock_response

            result = await ghsa_source.check_package(client, sample_package)

            assert len(result) == 1
            vuln = result[0]
            assert vuln.id == "GHSA-abcd-1234"
            assert vuln.severity == Severity.HIGH
            assert vuln.fixed_version == "2.31.0"

    def test_is_version_vulnerable(self, ghsa_source: GhsaSource) -> None:
        """Test version vulnerability checking."""
        # Version in range
        assert ghsa_source._is_version_vulnerable("2.0.0", "< 2.31.0") is True
        # Version at boundary
        assert ghsa_source._is_version_vulnerable("2.31.0", "< 2.31.0") is False
        # Version above range
        assert ghsa_source._is_version_vulnerable("3.0.0", "< 2.31.0") is False
        # Complex range
        assert ghsa_source._is_version_vulnerable("1.5.0", ">= 1.0.0, < 2.0.0") is True
        assert ghsa_source._is_version_vulnerable("0.5.0", ">= 1.0.0, < 2.0.0") is False


class TestRustSecSource:
    """Tests for RustSec Advisory Database source."""

    @pytest.fixture
    def rustsec_source(self) -> RustSecSource:
        """Create a RustSec source instance."""
        return RustSecSource()

    @pytest.fixture
    def rust_package(self) -> Package:
        """Create a sample Rust package for testing."""
        return Package(
            name="tokio",
            language="rust",
            current_version="1.0.0",
        )

    def test_source_name(self, rustsec_source: RustSecSource) -> None:
        """Test source name property."""
        assert rustsec_source.name == "rustsec"
        assert rustsec_source.display_name == "RustSec Advisory Database"

    @pytest.mark.asyncio
    async def test_check_package_wrong_language(self, rustsec_source: RustSecSource) -> None:
        """Test check_package returns empty for non-Rust packages."""
        pkg = Package(name="test", language="python", current_version="1.0.0")
        client = AsyncMock()
        result = await rustsec_source.check_package(client, pkg)
        assert result == []

    @pytest.mark.asyncio
    async def test_check_package_no_version(self, rustsec_source: RustSecSource) -> None:
        """Test check_package returns empty when no version."""
        pkg = Package(name="tokio", language="rust", current_version=None)
        client = AsyncMock()
        result = await rustsec_source.check_package(client, pkg)
        assert result == []

    @pytest.mark.asyncio
    async def test_check_package_no_advisories(
        self, rustsec_source: RustSecSource, rust_package: Package
    ) -> None:
        """Test check_package when no advisories exist for package."""
        # Mock crates.io response
        crates_response = MagicMock()
        crates_response.status_code = 200
        crates_response.json.return_value = {"crate": {"name": "tokio"}}

        # Mock GitHub API response (404 = no advisories)
        github_response = MagicMock()
        github_response.status_code = 404

        client = AsyncMock()
        client.get.side_effect = [crates_response, github_response]

        result = await rustsec_source.check_package(client, rust_package)
        assert result == []

    def test_version_matches_requirement(self, rustsec_source: RustSecSource) -> None:
        """Test semver requirement matching."""
        from packaging.version import Version

        v1_5 = Version("1.5.0")
        v2_0 = Version("2.0.0")
        v0_5 = Version("0.5.0")

        # Greater than or equal
        assert rustsec_source._version_matches_requirement(v1_5, ">= 1.0.0") is True
        assert rustsec_source._version_matches_requirement(v0_5, ">= 1.0.0") is False

        # Less than
        assert rustsec_source._version_matches_requirement(v1_5, "< 2.0.0") is True
        assert rustsec_source._version_matches_requirement(v2_0, "< 2.0.0") is False

        # Caret requirement
        assert rustsec_source._version_matches_requirement(v1_5, "^1.0.0") is True
        assert rustsec_source._version_matches_requirement(v2_0, "^1.0.0") is False

    def test_is_version_vulnerable(self, rustsec_source: RustSecSource) -> None:
        """Test version vulnerability checking."""
        # Version is in patched list
        assert rustsec_source._is_version_vulnerable("2.0.0", [">= 2.0.0"], []) is False
        # Version is not in patched list
        assert rustsec_source._is_version_vulnerable("1.5.0", [">= 2.0.0"], []) is True
        # Version is in unaffected list
        assert rustsec_source._is_version_vulnerable("0.5.0", [], ["< 1.0.0"]) is False


class TestVulnerabilityParsing:
    """Tests for vulnerability parsing edge cases."""

    def test_severity_from_cvss_edge_cases(self) -> None:
        """Test Severity.from_cvss with edge cases."""
        # 0.0 is technically no risk, but we map it to LOW
        assert Severity.from_cvss(0.0) == Severity.UNKNOWN
        assert Severity.from_cvss(10.0) == Severity.CRITICAL
        assert Severity.from_cvss(4.0) == Severity.MEDIUM
        assert Severity.from_cvss(7.0) == Severity.HIGH

    def test_severity_ordering(self) -> None:
        """Test that severity levels are properly ordered."""
        assert Severity.LOW < Severity.MEDIUM
        assert Severity.MEDIUM < Severity.HIGH
        assert Severity.HIGH < Severity.CRITICAL
        assert Severity.UNKNOWN < Severity.LOW
