"""Tests for core models."""

from depswiz.core.models import (
    CheckResult,
    LicenseCategory,
    LicenseInfo,
    Package,
    Severity,
    UpdateType,
)


class TestPackage:
    """Tests for the Package model."""

    def test_basic_package(self):
        pkg = Package(name="requests", current_version="2.28.0")
        assert pkg.name == "requests"
        assert pkg.current_version == "2.28.0"
        assert pkg.is_outdated is False

    def test_outdated_package(self):
        pkg = Package(
            name="requests",
            current_version="2.28.0",
            latest_version="2.31.0",
        )
        assert pkg.is_outdated is True

    def test_display_name_simple(self):
        pkg = Package(name="requests")
        assert pkg.display_name == "requests"

    def test_display_name_with_extras(self):
        pkg = Package(name="httpx", extras=["http2", "socks"])
        assert pkg.display_name == "httpx[http2,socks]"

    def test_with_latest_version(self):
        pkg = Package(name="requests", current_version="2.28.0")
        updated = pkg.with_latest_version("2.31.0")

        assert updated.latest_version == "2.31.0"
        assert updated.update_type == UpdateType.MINOR
        assert updated.name == pkg.name


class TestSeverity:
    """Tests for the Severity enum."""

    def test_from_cvss_critical(self):
        assert Severity.from_cvss(9.5) == Severity.CRITICAL

    def test_from_cvss_high(self):
        assert Severity.from_cvss(7.5) == Severity.HIGH

    def test_from_cvss_medium(self):
        assert Severity.from_cvss(5.0) == Severity.MEDIUM

    def test_from_cvss_low(self):
        assert Severity.from_cvss(2.5) == Severity.LOW

    def test_severity_comparison(self):
        assert Severity.LOW < Severity.MEDIUM
        assert Severity.MEDIUM < Severity.HIGH
        assert Severity.HIGH < Severity.CRITICAL


class TestLicenseInfo:
    """Tests for the LicenseInfo model."""

    def test_from_spdx_mit(self):
        license_info = LicenseInfo.from_spdx("MIT")
        assert license_info.spdx_id == "MIT"
        assert license_info.category == LicenseCategory.PERMISSIVE
        assert license_info.is_copyleft is False

    def test_from_spdx_gpl(self):
        license_info = LicenseInfo.from_spdx("GPL-3.0-only")
        assert license_info.spdx_id == "GPL-3.0-only"
        assert license_info.category == LicenseCategory.STRONG_COPYLEFT
        assert license_info.is_copyleft is True

    def test_from_spdx_lgpl(self):
        license_info = LicenseInfo.from_spdx("LGPL-3.0-only")
        assert license_info.spdx_id == "LGPL-3.0-only"
        assert license_info.category == LicenseCategory.WEAK_COPYLEFT
        assert license_info.is_copyleft is True


class TestCheckResult:
    """Tests for the CheckResult model."""

    def test_empty_result(self):
        result = CheckResult()
        assert result.total_packages == 0
        assert result.outdated_packages == []

    def test_with_packages(self):
        packages = [
            Package(name="pkg1", current_version="1.0.0", latest_version="1.0.0"),
            Package(
                name="pkg2",
                current_version="1.0.0",
                latest_version="2.0.0",
                update_type=UpdateType.MAJOR,
            ),
            Package(
                name="pkg3",
                current_version="1.0.0",
                latest_version="1.1.0",
                update_type=UpdateType.MINOR,
            ),
        ]
        result = CheckResult(packages=packages)

        assert result.total_packages == 3
        assert len(result.outdated_packages) == 2
        assert len(result.up_to_date_packages) == 1

    def test_update_breakdown(self):
        packages = [
            Package(
                name="pkg1",
                current_version="1.0.0",
                latest_version="2.0.0",
                update_type=UpdateType.MAJOR,
            ),
            Package(
                name="pkg2",
                current_version="1.0.0",
                latest_version="1.1.0",
                update_type=UpdateType.MINOR,
            ),
            Package(
                name="pkg3",
                current_version="1.0.0",
                latest_version="1.0.1",
                update_type=UpdateType.PATCH,
            ),
            Package(
                name="pkg4",
                current_version="1.0.0",
                latest_version="1.0.2",
                update_type=UpdateType.PATCH,
            ),
        ]
        result = CheckResult(packages=packages)
        breakdown = result.update_breakdown

        assert breakdown[UpdateType.MAJOR] == 1
        assert breakdown[UpdateType.MINOR] == 1
        assert breakdown[UpdateType.PATCH] == 2
