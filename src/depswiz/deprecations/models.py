"""Data models for deprecation detection."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path


class DeprecationStatus(Enum):
    """Deprecation severity/status levels."""

    DEPRECATED = "deprecated"  # Marked @Deprecated, still works
    REMOVAL_PLANNED = "removal"  # Has scheduled removal version
    BREAKING_SOON = "breaking"  # Will break in next major version
    INFO = "info"  # Informational hint

    @classmethod
    def from_analyzer_severity(cls, severity: str) -> DeprecationStatus:
        """Map dart analyzer severity to deprecation status.

        Args:
            severity: Analyzer severity (WARNING, INFO, ERROR)

        Returns:
            Corresponding deprecation status
        """
        severity_map = {
            "ERROR": cls.BREAKING_SOON,
            "WARNING": cls.DEPRECATED,
            "INFO": cls.INFO,
        }
        return severity_map.get(severity.upper(), cls.DEPRECATED)

    def __lt__(self, other: DeprecationStatus) -> bool:
        """Compare status levels for filtering."""
        if not isinstance(other, DeprecationStatus):
            return NotImplemented
        order = [self.INFO, self.DEPRECATED, self.REMOVAL_PLANNED, self.BREAKING_SOON]
        return order.index(self) < order.index(other)

    def __le__(self, other: DeprecationStatus) -> bool:
        """Compare status levels for filtering."""
        if not isinstance(other, DeprecationStatus):
            return NotImplemented
        return self == other or self < other


@dataclass
class Deprecation:
    """A single deprecation warning from analysis."""

    rule_id: str  # e.g., "deprecated_member_use"
    message: str  # Full deprecation message
    file_path: Path  # Source file location
    line: int  # Line number (1-indexed)
    column: int  # Column number (1-indexed)
    status: DeprecationStatus = DeprecationStatus.DEPRECATED

    # Optional enrichment
    package: str | None = None  # Which package introduced this
    replacement: str | None = None  # Suggested replacement
    fix_available: bool = False  # Can dart fix handle this?
    references: list[str] = field(default_factory=list)  # Migration guide URLs

    @property
    def location(self) -> str:
        """Get formatted file:line:column location."""
        return f"{self.file_path}:{self.line}:{self.column}"

    @property
    def short_location(self) -> str:
        """Get short location (filename:line)."""
        return f"{self.file_path.name}:{self.line}"


@dataclass
class DeprecationResult:
    """Result of deprecation scanning."""

    path: Path  # Project path
    deprecations: list[Deprecation] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

    # Tool versions
    dart_version: str | None = None
    flutter_version: str | None = None

    # Fix statistics
    fixable_count: int = 0

    @property
    def total_count(self) -> int:
        """Total number of deprecations found."""
        return len(self.deprecations)

    @property
    def by_status(self) -> dict[DeprecationStatus, int]:
        """Count deprecations by status."""
        counts: dict[DeprecationStatus, int] = {}
        for dep in self.deprecations:
            counts[dep.status] = counts.get(dep.status, 0) + 1
        return counts

    @property
    def by_package(self) -> dict[str, int]:
        """Count deprecations by source package."""
        counts: dict[str, int] = {}
        for dep in self.deprecations:
            pkg = dep.package or "unknown"
            counts[pkg] = counts.get(pkg, 0) + 1
        return counts

    @property
    def by_rule(self) -> dict[str, int]:
        """Count deprecations by rule ID."""
        counts: dict[str, int] = {}
        for dep in self.deprecations:
            counts[dep.rule_id] = counts.get(dep.rule_id, 0) + 1
        return counts

    @property
    def by_file(self) -> dict[Path, list[Deprecation]]:
        """Group deprecations by file."""
        groups: dict[Path, list[Deprecation]] = {}
        for dep in self.deprecations:
            if dep.file_path not in groups:
                groups[dep.file_path] = []
            groups[dep.file_path].append(dep)
        return groups

    @property
    def breaking_count(self) -> int:
        """Count of breaking/removal deprecations."""
        return sum(
            1
            for d in self.deprecations
            if d.status in (DeprecationStatus.BREAKING_SOON, DeprecationStatus.REMOVAL_PLANNED)
        )

    def filter_by_status(self, min_status: DeprecationStatus) -> list[Deprecation]:
        """Filter deprecations by minimum status level.

        Args:
            min_status: Minimum status to include

        Returns:
            Filtered list of deprecations
        """
        return [d for d in self.deprecations if d.status >= min_status]

    def filter_fixable(self) -> list[Deprecation]:
        """Get only auto-fixable deprecations."""
        return [d for d in self.deprecations if d.fix_available]
