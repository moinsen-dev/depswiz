"""Core data models for depswiz."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


class UpdateType(Enum):
    """Type of version update."""

    PATCH = "patch"
    MINOR = "minor"
    MAJOR = "major"

    def __str__(self) -> str:
        return self.value


class Severity(Enum):
    """Vulnerability severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"

    def __str__(self) -> str:
        return self.value

    @classmethod
    def from_cvss(cls, score: float) -> "Severity":
        """Convert CVSS score to severity level."""
        if score >= 9.0:
            return cls.CRITICAL
        if score >= 7.0:
            return cls.HIGH
        if score >= 4.0:
            return cls.MEDIUM
        if score > 0.0:
            return cls.LOW
        return cls.UNKNOWN

    def __lt__(self, other: "Severity") -> bool:
        order = [Severity.UNKNOWN, Severity.LOW, Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL]
        return order.index(self) < order.index(other)

    def __le__(self, other: "Severity") -> bool:
        return self == other or self < other


class LicenseCategory(Enum):
    """License category classification."""

    PERMISSIVE = "permissive"
    WEAK_COPYLEFT = "weak_copyleft"
    STRONG_COPYLEFT = "strong_copyleft"
    PUBLIC_DOMAIN = "public_domain"
    PROPRIETARY = "proprietary"
    UNKNOWN = "unknown"


@dataclass
class Package:
    """Represents a dependency package."""

    name: str
    current_version: str | None = None
    constraint: str | None = None
    latest_version: str | None = None
    update_type: UpdateType | None = None
    source_file: Path | None = None
    extras: list[str] | None = None
    language: str | None = None
    is_dev: bool = False
    license_info: Optional["LicenseInfo"] = None
    vulnerabilities: list["Vulnerability"] = field(default_factory=list)

    @property
    def is_outdated(self) -> bool:
        """Check if package is outdated."""
        if self.current_version is None or self.latest_version is None:
            return False
        return self.current_version != self.latest_version

    @property
    def has_vulnerabilities(self) -> bool:
        """Check if package has known vulnerabilities."""
        return len(self.vulnerabilities) > 0

    @property
    def display_name(self) -> str:
        """Get display name with extras if present."""
        if self.extras:
            return f"{self.name}[{','.join(self.extras)}]"
        return self.name

    def with_latest_version(self, version: str) -> "Package":
        """Return a copy with the latest version set."""
        from depswiz.core.version import determine_update_type

        update_type = None
        if self.current_version and version:
            update_type = determine_update_type(self.current_version, version)

        return Package(
            name=self.name,
            current_version=self.current_version,
            constraint=self.constraint,
            latest_version=version,
            update_type=update_type,
            source_file=self.source_file,
            extras=self.extras,
            language=self.language,
            is_dev=self.is_dev,
            license_info=self.license_info,
            vulnerabilities=self.vulnerabilities,
        )


@dataclass
class Vulnerability:
    """Represents a security vulnerability."""

    id: str
    title: str
    description: str
    severity: Severity
    affected_versions: str
    source: str
    cvss_score: float | None = None
    cvss_vector: str | None = None
    fixed_version: str | None = None
    workaround: str | None = None
    published: datetime | None = None
    modified: datetime | None = None
    references: list[str] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)
    cwe_ids: list[str] = field(default_factory=list)

    @property
    def display_id(self) -> str:
        """Get the primary ID for display."""
        return self.id

    @property
    def all_ids(self) -> list[str]:
        """Get all IDs including aliases."""
        return [self.id, *self.aliases]


@dataclass
class LicenseInfo:
    """License information for a package."""

    name: str
    spdx_id: str | None = None
    url: str | None = None
    is_osi_approved: bool = False
    is_copyleft: bool = False
    category: LicenseCategory = LicenseCategory.UNKNOWN

    @classmethod
    def from_spdx(cls, spdx_id: str) -> "LicenseInfo":
        """Create LicenseInfo from SPDX identifier."""
        # Permissive licenses
        permissive = {
            "MIT",
            "Apache-2.0",
            "BSD-2-Clause",
            "BSD-3-Clause",
            "ISC",
            "Unlicense",
            "CC0-1.0",
            "0BSD",
            "BlueOak-1.0.0",
            "MIT-0",
        }
        # Weak copyleft
        weak_copyleft = {
            "LGPL-2.1-only",
            "LGPL-2.1-or-later",
            "LGPL-3.0-only",
            "LGPL-3.0-or-later",
            "MPL-2.0",
            "EPL-2.0",
        }
        # Strong copyleft
        strong_copyleft = {
            "GPL-2.0-only",
            "GPL-2.0-or-later",
            "GPL-3.0-only",
            "GPL-3.0-or-later",
            "AGPL-3.0-only",
            "AGPL-3.0-or-later",
        }
        # Public domain
        public_domain = {"Unlicense", "CC0-1.0", "WTFPL"}

        is_copyleft = spdx_id in weak_copyleft or spdx_id in strong_copyleft

        if spdx_id in permissive:
            category = LicenseCategory.PERMISSIVE
        elif spdx_id in weak_copyleft:
            category = LicenseCategory.WEAK_COPYLEFT
        elif spdx_id in strong_copyleft:
            category = LicenseCategory.STRONG_COPYLEFT
        elif spdx_id in public_domain:
            category = LicenseCategory.PUBLIC_DOMAIN
        else:
            category = LicenseCategory.UNKNOWN

        return cls(
            name=spdx_id,
            spdx_id=spdx_id,
            is_osi_approved=spdx_id in permissive or spdx_id in weak_copyleft,
            is_copyleft=is_copyleft,
            category=category,
        )


@dataclass
class CheckResult:
    """Result of a dependency check operation."""

    packages: list[Package] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    path: Path | None = None

    @property
    def total_packages(self) -> int:
        """Total number of packages checked."""
        return len(self.packages)

    @property
    def outdated_packages(self) -> list[Package]:
        """List of outdated packages."""
        return [p for p in self.packages if p.is_outdated]

    @property
    def up_to_date_packages(self) -> list[Package]:
        """List of up-to-date packages."""
        return [p for p in self.packages if not p.is_outdated]

    @property
    def update_breakdown(self) -> dict[UpdateType, int]:
        """Breakdown of updates by type."""
        breakdown: dict[UpdateType, int] = {
            UpdateType.MAJOR: 0,
            UpdateType.MINOR: 0,
            UpdateType.PATCH: 0,
        }
        for pkg in self.outdated_packages:
            if pkg.update_type:
                breakdown[pkg.update_type] += 1
        return breakdown


@dataclass
class AuditResult:
    """Result of a security audit operation."""

    packages: list[Package] = field(default_factory=list)
    vulnerabilities: list[tuple[Package, Vulnerability]] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    path: Path | None = None

    @property
    def total_vulnerabilities(self) -> int:
        """Total number of vulnerabilities found."""
        return len(self.vulnerabilities)

    @property
    def critical_count(self) -> int:
        """Number of critical vulnerabilities."""
        return sum(1 for _, v in self.vulnerabilities if v.severity == Severity.CRITICAL)

    @property
    def high_count(self) -> int:
        """Number of high severity vulnerabilities."""
        return sum(1 for _, v in self.vulnerabilities if v.severity == Severity.HIGH)

    @property
    def medium_count(self) -> int:
        """Number of medium severity vulnerabilities."""
        return sum(1 for _, v in self.vulnerabilities if v.severity == Severity.MEDIUM)

    @property
    def low_count(self) -> int:
        """Number of low severity vulnerabilities."""
        return sum(1 for _, v in self.vulnerabilities if v.severity == Severity.LOW)

    def vulnerabilities_by_severity(
        self, min_severity: Severity
    ) -> list[tuple[Package, Vulnerability]]:
        """Get vulnerabilities at or above the specified severity."""
        return [(p, v) for p, v in self.vulnerabilities if v.severity >= min_severity]


@dataclass
class LicenseResult:
    """Result of a license compliance check."""

    packages: list[Package] = field(default_factory=list)
    violations: list[tuple[Package, str]] = field(default_factory=list)
    warnings: list[tuple[Package, str]] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    path: Path | None = None

    @property
    def has_violations(self) -> bool:
        """Check if there are any license violations."""
        return len(self.violations) > 0

    @property
    def license_summary(self) -> dict[str, int]:
        """Summary of licenses by SPDX ID."""
        summary: dict[str, int] = {}
        for pkg in self.packages:
            if pkg.license_info and pkg.license_info.spdx_id:
                spdx_id = pkg.license_info.spdx_id
                summary[spdx_id] = summary.get(spdx_id, 0) + 1
            else:
                summary["UNKNOWN"] = summary.get("UNKNOWN", 0) + 1
        return summary
