"""JSON output formatter for depswiz."""

import json
from typing import Any

from depswiz import __version__
from depswiz.cli.formatters.base import OutputFormatter
from depswiz.core.models import (
    AuditResult,
    CheckResult,
    LicenseResult,
    Package,
    UpdateType,
    Vulnerability,
)


class JsonFormatter(OutputFormatter):
    """JSON output formatter for machine parsing."""

    def format_check_result(self, result: CheckResult, warn_breaking: bool = True) -> str:
        """Format a check result as JSON."""
        data = {
            "version": __version__,
            "timestamp": result.timestamp.isoformat(),
            "command": "check",
            "status": "outdated" if result.outdated_packages else "up_to_date",
            "path": str(result.path) if result.path else None,
            "summary": {
                "total_packages": result.total_packages,
                "outdated_packages": len(result.outdated_packages),
                "up_to_date": len(result.up_to_date_packages),
                "update_breakdown": {
                    ut.value: count for ut, count in result.update_breakdown.items()
                },
            },
            "packages": [self._package_to_dict(pkg) for pkg in result.packages],
        }

        return json.dumps(data, indent=2, default=str)

    def format_audit_result(self, result: AuditResult, show_fix: bool = False) -> str:
        """Format an audit result as JSON."""
        data = {
            "version": __version__,
            "timestamp": result.timestamp.isoformat(),
            "command": "audit",
            "status": "vulnerable" if result.vulnerabilities else "clean",
            "path": str(result.path) if result.path else None,
            "summary": {
                "total_packages": len(result.packages),
                "total_vulnerabilities": result.total_vulnerabilities,
                "by_severity": {
                    "critical": result.critical_count,
                    "high": result.high_count,
                    "medium": result.medium_count,
                    "low": result.low_count,
                },
            },
            "vulnerabilities": [
                {
                    "package": self._package_to_dict(pkg),
                    "vulnerability": self._vulnerability_to_dict(vuln),
                }
                for pkg, vuln in result.vulnerabilities
            ],
        }

        return json.dumps(data, indent=2, default=str)

    def format_license_result(self, result: LicenseResult, summary_only: bool = False) -> str:
        """Format a license result as JSON."""
        data: dict[str, Any] = {
            "version": __version__,
            "timestamp": result.timestamp.isoformat(),
            "command": "licenses",
            "status": "violation" if result.has_violations else "compliant",
            "path": str(result.path) if result.path else None,
            "summary": result.license_summary,
            "violations": [
                {"package": pkg.name, "reason": reason} for pkg, reason in result.violations
            ],
            "warnings": [
                {"package": pkg.name, "reason": reason} for pkg, reason in result.warnings
            ],
        }

        if not summary_only:
            data["packages"] = [
                {
                    "name": pkg.name,
                    "version": pkg.current_version,
                    "license": {
                        "spdx_id": pkg.license_info.spdx_id if pkg.license_info else None,
                        "name": pkg.license_info.name if pkg.license_info else None,
                        "category": pkg.license_info.category.value if pkg.license_info else None,
                        "is_copyleft": pkg.license_info.is_copyleft if pkg.license_info else None,
                    }
                    if pkg.license_info
                    else None,
                }
                for pkg in result.packages
            ]

        return json.dumps(data, indent=2, default=str)

    def _package_to_dict(self, pkg: Package) -> dict[str, Any]:
        """Convert a Package to a dictionary."""
        return {
            "name": pkg.name,
            "language": pkg.language,
            "source_file": str(pkg.source_file) if pkg.source_file else None,
            "constraint": pkg.constraint,
            "current_version": pkg.current_version,
            "latest_version": pkg.latest_version,
            "update_type": pkg.update_type.value if pkg.update_type else None,
            "is_outdated": pkg.is_outdated,
            "is_dev": pkg.is_dev,
            "extras": pkg.extras,
            "license": pkg.license_info.spdx_id if pkg.license_info else None,
            "has_vulnerabilities": pkg.has_vulnerabilities,
        }

    def _vulnerability_to_dict(self, vuln: Vulnerability) -> dict[str, Any]:
        """Convert a Vulnerability to a dictionary."""
        return {
            "id": vuln.id,
            "aliases": vuln.aliases,
            "severity": vuln.severity.value,
            "cvss_score": vuln.cvss_score,
            "cvss_vector": vuln.cvss_vector,
            "title": vuln.title,
            "description": vuln.description,
            "affected_versions": vuln.affected_versions,
            "fixed_version": vuln.fixed_version,
            "source": vuln.source,
            "references": vuln.references,
            "published": vuln.published.isoformat() if vuln.published else None,
        }

    def format_comprehensive_scan(
        self,
        check_result: CheckResult,
        audit_result: AuditResult,
        license_result: LicenseResult,
    ) -> str:
        """Format comprehensive scan results as JSON."""
        # Determine overall status
        has_outdated = len(check_result.outdated_packages) > 0
        has_vulns = audit_result.total_vulnerabilities > 0
        has_violations = license_result.has_violations

        if has_vulns or has_violations:
            status = "critical"
        elif has_outdated:
            status = "warning"
        else:
            status = "ok"

        data = {
            "version": __version__,
            "timestamp": check_result.timestamp.isoformat(),
            "command": "scan",
            "status": status,
            "path": str(check_result.path) if check_result.path else None,
            "summary": {
                "total_packages": check_result.total_packages,
                "outdated_packages": len(check_result.outdated_packages),
                "update_breakdown": {
                    ut.value: count for ut, count in check_result.update_breakdown.items()
                },
                "vulnerabilities": {
                    "total": audit_result.total_vulnerabilities,
                    "critical": audit_result.critical_count,
                    "high": audit_result.high_count,
                    "medium": audit_result.medium_count,
                    "low": audit_result.low_count,
                },
                "licenses": {
                    "violations": len(license_result.violations),
                    "warnings": len(license_result.warnings),
                    "distribution": license_result.license_summary,
                },
            },
            "outdated": [self._package_to_dict(pkg) for pkg in check_result.outdated_packages],
            "vulnerabilities": [
                {
                    "package": self._package_to_dict(pkg),
                    "vulnerability": self._vulnerability_to_dict(vuln),
                }
                for pkg, vuln in audit_result.vulnerabilities
            ],
            "license_violations": [
                {"package": pkg.name, "reason": reason}
                for pkg, reason in license_result.violations
            ],
            "license_warnings": [
                {"package": pkg.name, "reason": reason}
                for pkg, reason in license_result.warnings
            ],
        }

        return json.dumps(data, indent=2, default=str)
