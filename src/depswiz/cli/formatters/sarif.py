"""SARIF output formatter for depswiz.

SARIF (Static Analysis Results Interchange Format) is a standard format
for static analysis tools, enabling integration with GitHub Code Scanning,
VS Code, and other security tools.

Reference: https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html
"""

import json
from typing import Any

from depswiz import __version__
from depswiz.cli.formatters.base import OutputFormatter
from depswiz.core.models import (
    AuditResult,
    CheckResult,
    LicenseResult,
    Package,
    Severity,
    Vulnerability,
)


class SarifFormatter(OutputFormatter):
    """SARIF 2.1.0 output formatter for security tool integration."""

    SARIF_VERSION = "2.1.0"
    SCHEMA_URI = "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json"

    def format_check_result(self, result: CheckResult, warn_breaking: bool = True) -> str:
        """Format a check result as SARIF.

        Outdated dependencies are reported as warnings.
        """
        rules: list[dict[str, Any]] = []
        results: list[dict[str, Any]] = []

        # Create a rule for outdated dependencies
        rules.append({
            "id": "depswiz/outdated-dependency",
            "name": "OutdatedDependency",
            "shortDescription": {"text": "Outdated dependency detected"},
            "fullDescription": {
                "text": "A dependency has a newer version available. Keeping dependencies updated helps ensure you have the latest security fixes and features."
            },
            "helpUri": "https://github.com/moinsen-dev/depswiz",
            "properties": {
                "tags": ["security", "maintainability"],
            },
        })

        for pkg in result.outdated_packages:
            sarif_result = self._create_outdated_result(pkg)
            results.append(sarif_result)

        return self._create_sarif_document(
            tool_name="depswiz-check",
            rules=rules,
            results=results,
        )

    def format_audit_result(self, result: AuditResult, show_fix: bool = False) -> str:
        """Format an audit result as SARIF.

        Vulnerabilities are reported with their severity level.
        """
        rules: list[dict[str, Any]] = []
        results: list[dict[str, Any]] = []
        seen_rules: set[str] = set()

        for pkg, vuln in result.vulnerabilities:
            # Create rule for this vulnerability type if not seen
            rule_id = f"depswiz/vuln/{vuln.id}"
            if rule_id not in seen_rules:
                rules.append(self._create_vulnerability_rule(vuln))
                seen_rules.add(rule_id)

            # Create result for this occurrence
            sarif_result = self._create_vulnerability_result(pkg, vuln)
            results.append(sarif_result)

        return self._create_sarif_document(
            tool_name="depswiz-audit",
            rules=rules,
            results=results,
        )

    def format_license_result(self, result: LicenseResult, summary_only: bool = False) -> str:
        """Format a license result as SARIF.

        License violations are reported as errors, warnings as notes.
        """
        rules: list[dict[str, Any]] = []
        results: list[dict[str, Any]] = []

        # Rule for license violations
        rules.append({
            "id": "depswiz/license-violation",
            "name": "LicenseViolation",
            "shortDescription": {"text": "License policy violation"},
            "fullDescription": {
                "text": "A dependency uses a license that violates your configured license policy."
            },
            "helpUri": "https://github.com/moinsen-dev/depswiz",
            "defaultConfiguration": {"level": "error"},
            "properties": {
                "tags": ["license", "compliance"],
            },
        })

        # Rule for license warnings
        rules.append({
            "id": "depswiz/license-warning",
            "name": "LicenseWarning",
            "shortDescription": {"text": "License compliance warning"},
            "fullDescription": {
                "text": "A dependency uses a license that may require attention (e.g., copyleft)."
            },
            "helpUri": "https://github.com/moinsen-dev/depswiz",
            "defaultConfiguration": {"level": "warning"},
            "properties": {
                "tags": ["license", "compliance"],
            },
        })

        for pkg, reason in result.violations:
            results.append({
                "ruleId": "depswiz/license-violation",
                "level": "error",
                "message": {
                    "text": f"License violation in {pkg.name}: {reason}",
                },
                "locations": [self._create_package_location(pkg)],
            })

        for pkg, reason in result.warnings:
            results.append({
                "ruleId": "depswiz/license-warning",
                "level": "warning",
                "message": {
                    "text": f"License warning for {pkg.name}: {reason}",
                },
                "locations": [self._create_package_location(pkg)],
            })

        return self._create_sarif_document(
            tool_name="depswiz-licenses",
            rules=rules,
            results=results,
        )

    def format_comprehensive_scan(
        self,
        check_result: CheckResult,
        audit_result: AuditResult,
        license_result: LicenseResult,
    ) -> str:
        """Format comprehensive scan results as a single SARIF document."""
        rules: list[dict[str, Any]] = []
        results: list[dict[str, Any]] = []
        seen_rules: set[str] = set()

        # Add outdated dependency rule
        rules.append({
            "id": "depswiz/outdated-dependency",
            "name": "OutdatedDependency",
            "shortDescription": {"text": "Outdated dependency detected"},
            "fullDescription": {
                "text": "A dependency has a newer version available."
            },
            "helpUri": "https://github.com/moinsen-dev/depswiz",
            "defaultConfiguration": {"level": "warning"},
            "properties": {"tags": ["security", "maintainability"]},
        })
        seen_rules.add("depswiz/outdated-dependency")

        # Add license rules
        rules.append({
            "id": "depswiz/license-violation",
            "name": "LicenseViolation",
            "shortDescription": {"text": "License policy violation"},
            "fullDescription": {"text": "A dependency violates your license policy."},
            "helpUri": "https://github.com/moinsen-dev/depswiz",
            "defaultConfiguration": {"level": "error"},
            "properties": {"tags": ["license", "compliance"]},
        })
        seen_rules.add("depswiz/license-violation")

        rules.append({
            "id": "depswiz/license-warning",
            "name": "LicenseWarning",
            "shortDescription": {"text": "License compliance warning"},
            "fullDescription": {"text": "A dependency may require license attention."},
            "helpUri": "https://github.com/moinsen-dev/depswiz",
            "defaultConfiguration": {"level": "warning"},
            "properties": {"tags": ["license", "compliance"]},
        })
        seen_rules.add("depswiz/license-warning")

        # Add vulnerability rules
        for _pkg, vuln in audit_result.vulnerabilities:
            rule_id = f"depswiz/vuln/{vuln.id}"
            if rule_id not in seen_rules:
                rules.append(self._create_vulnerability_rule(vuln))
                seen_rules.add(rule_id)

        # Add outdated dependency results
        for pkg in check_result.outdated_packages:
            results.append(self._create_outdated_result(pkg))

        # Add vulnerability results
        for pkg, vuln in audit_result.vulnerabilities:
            results.append(self._create_vulnerability_result(pkg, vuln))

        # Add license results
        for pkg, reason in license_result.violations:
            results.append({
                "ruleId": "depswiz/license-violation",
                "level": "error",
                "message": {"text": f"License violation in {pkg.name}: {reason}"},
                "locations": [self._create_package_location(pkg)],
            })

        for pkg, reason in license_result.warnings:
            results.append({
                "ruleId": "depswiz/license-warning",
                "level": "warning",
                "message": {"text": f"License warning for {pkg.name}: {reason}"},
                "locations": [self._create_package_location(pkg)],
            })

        return self._create_sarif_document(
            tool_name="depswiz",
            rules=rules,
            results=results,
        )

    def _create_sarif_document(
        self,
        tool_name: str,
        rules: list[dict[str, Any]],
        results: list[dict[str, Any]],
    ) -> str:
        """Create a complete SARIF document."""
        sarif = {
            "$schema": self.SCHEMA_URI,
            "version": self.SARIF_VERSION,
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": tool_name,
                            "version": __version__,
                            "informationUri": "https://github.com/moinsen-dev/depswiz",
                            "rules": rules,
                        }
                    },
                    "results": results,
                }
            ],
        }
        return json.dumps(sarif, indent=2)

    def _create_vulnerability_rule(self, vuln: Vulnerability) -> dict[str, Any]:
        """Create a SARIF rule for a vulnerability."""
        level = self._severity_to_sarif_level(vuln.severity)

        rule: dict[str, Any] = {
            "id": f"depswiz/vuln/{vuln.id}",
            "name": vuln.id,
            "shortDescription": {"text": vuln.title or vuln.id},
            "fullDescription": {"text": vuln.description or vuln.title or vuln.id},
            "helpUri": vuln.references[0] if vuln.references else "https://osv.dev",
            "defaultConfiguration": {"level": level},
            "properties": {
                "tags": ["security", "vulnerability"],
                "security-severity": str(vuln.cvss_score) if vuln.cvss_score else "0.0",
            },
        }

        if vuln.cwe_ids:
            rule["properties"]["cwe"] = vuln.cwe_ids

        return rule

    def _create_vulnerability_result(
        self, pkg: Package, vuln: Vulnerability
    ) -> dict[str, Any]:
        """Create a SARIF result for a vulnerability."""
        level = self._severity_to_sarif_level(vuln.severity)

        message_parts = [f"Vulnerability {vuln.id} found in {pkg.name}@{pkg.current_version}"]
        if vuln.title:
            message_parts.append(f": {vuln.title}")
        if vuln.fixed_version:
            message_parts.append(f". Fixed in version {vuln.fixed_version}")

        result: dict[str, Any] = {
            "ruleId": f"depswiz/vuln/{vuln.id}",
            "level": level,
            "message": {"text": "".join(message_parts)},
            "locations": [self._create_package_location(pkg)],
        }

        # Add fingerprint for deduplication
        result["partialFingerprints"] = {
            "primaryLocationLineHash": f"{pkg.name}:{pkg.current_version}:{vuln.id}"
        }

        # Add related locations for references
        if vuln.references:
            result["relatedLocations"] = [
                {
                    "id": i,
                    "message": {"text": f"Reference: {ref}"},
                    "physicalLocation": {
                        "artifactLocation": {"uri": ref}
                    },
                }
                for i, ref in enumerate(vuln.references[:3])
            ]

        return result

    def _create_outdated_result(self, pkg: Package) -> dict[str, Any]:
        """Create a SARIF result for an outdated dependency."""
        update_type = pkg.update_type.value if pkg.update_type else "update"

        return {
            "ruleId": "depswiz/outdated-dependency",
            "level": "warning",
            "message": {
                "text": f"{pkg.name} {pkg.current_version} -> {pkg.latest_version} ({update_type} update available)"
            },
            "locations": [self._create_package_location(pkg)],
            "partialFingerprints": {
                "primaryLocationLineHash": f"{pkg.name}:{pkg.current_version}"
            },
        }

    def _create_package_location(self, pkg: Package) -> dict[str, Any]:
        """Create a SARIF location for a package."""
        if pkg.source_file:
            return {
                "physicalLocation": {
                    "artifactLocation": {
                        "uri": str(pkg.source_file),
                        "uriBaseId": "%SRCROOT%",
                    }
                },
                "logicalLocations": [
                    {
                        "name": pkg.name,
                        "kind": "package",
                        "fullyQualifiedName": f"{pkg.language}/{pkg.name}" if pkg.language else pkg.name,
                    }
                ],
            }
        else:
            return {
                "logicalLocations": [
                    {
                        "name": pkg.name,
                        "kind": "package",
                        "fullyQualifiedName": f"{pkg.language}/{pkg.name}" if pkg.language else pkg.name,
                    }
                ]
            }

    def _severity_to_sarif_level(self, severity: Severity) -> str:
        """Convert depswiz severity to SARIF level."""
        mapping = {
            Severity.CRITICAL: "error",
            Severity.HIGH: "error",
            Severity.MEDIUM: "warning",
            Severity.LOW: "note",
            Severity.UNKNOWN: "none",
        }
        return mapping.get(severity, "warning")
