"""Data models for development tools version checking."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ToolStatus(Enum):
    """Status of a development tool."""

    UP_TO_DATE = "up_to_date"
    UPDATE_AVAILABLE = "update_available"
    NOT_INSTALLED = "not_installed"
    ERROR = "error"


class Platform(Enum):
    """Operating system platform."""

    MACOS = "macos"
    LINUX = "linux"
    WINDOWS = "windows"
    UNKNOWN = "unknown"


@dataclass
class ToolVersion:
    """Represents a tool version."""

    major: int
    minor: int
    patch: int
    prerelease: str = ""
    build: str = ""

    @classmethod
    def parse(cls, version_str: str) -> Optional["ToolVersion"]:
        """Parse a version string like 'v1.2.3' or '1.2.3-beta'.

        Returns None if parsing fails.
        """
        if not version_str:
            return None

        # Strip leading 'v' or 'V'
        version_str = version_str.lstrip("vV").strip()

        # Handle build metadata (e.g., 1.2.3+build)
        build = ""
        if "+" in version_str:
            version_str, build = version_str.split("+", 1)

        # Handle prerelease (e.g., 1.2.3-beta.1)
        prerelease = ""
        if "-" in version_str:
            version_str, prerelease = version_str.split("-", 1)

        # Parse major.minor.patch
        parts = version_str.split(".")
        try:
            major = int(parts[0]) if len(parts) > 0 else 0
            minor = int(parts[1]) if len(parts) > 1 else 0
            patch = int(parts[2]) if len(parts) > 2 else 0
            return cls(
                major=major,
                minor=minor,
                patch=patch,
                prerelease=prerelease,
                build=build,
            )
        except (ValueError, IndexError):
            return None

    def __str__(self) -> str:
        """Return version as string."""
        version = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            version += f"-{self.prerelease}"
        if self.build:
            version += f"+{self.build}"
        return version

    def __lt__(self, other: "ToolVersion") -> bool:
        """Compare versions."""
        if not isinstance(other, ToolVersion):
            return NotImplemented

        # Compare major.minor.patch
        self_tuple = (self.major, self.minor, self.patch)
        other_tuple = (other.major, other.minor, other.patch)

        if self_tuple != other_tuple:
            return self_tuple < other_tuple

        # If base versions are equal, prereleases are less than non-prereleases
        if self.prerelease and not other.prerelease:
            return True
        if not self.prerelease and other.prerelease:
            return False

        # Both have prereleases, compare lexicographically
        return self.prerelease < other.prerelease

    def __eq__(self, other: object) -> bool:
        """Check version equality."""
        if not isinstance(other, ToolVersion):
            return NotImplemented
        return (
            self.major == other.major
            and self.minor == other.minor
            and self.patch == other.patch
            and self.prerelease == other.prerelease
        )

    def __le__(self, other: "ToolVersion") -> bool:
        return self == other or self < other

    def __gt__(self, other: "ToolVersion") -> bool:
        return not self <= other

    def __ge__(self, other: "ToolVersion") -> bool:
        return not self < other


@dataclass
class ToolDefinition:
    """Definition of a development tool for version checking."""

    name: str
    display_name: str
    version_command: list[str]
    version_regex: str
    github_repo: str | None = None
    official_api_url: str | None = None
    project_indicators: list[str] = field(default_factory=list)
    update_instructions: dict[str, str] = field(default_factory=dict)
    related_tools: list[str] = field(default_factory=list)


@dataclass
class Tool:
    """Represents a development tool with version information."""

    name: str
    display_name: str
    current_version: ToolVersion | None = None
    latest_version: ToolVersion | None = None
    status: ToolStatus = ToolStatus.NOT_INSTALLED
    error_message: str = ""
    update_instruction: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON output."""
        return {
            "name": self.name,
            "display_name": self.display_name,
            "current_version": str(self.current_version) if self.current_version else None,
            "latest_version": str(self.latest_version) if self.latest_version else None,
            "status": self.status.value,
            "error_message": self.error_message,
            "update_instruction": self.update_instruction,
        }


@dataclass
class ToolsCheckResult:
    """Result of checking development tools."""

    tools: list[Tool]
    platform: Platform

    @property
    def updates_available(self) -> int:
        """Count of tools with updates available."""
        return sum(1 for t in self.tools if t.status == ToolStatus.UPDATE_AVAILABLE)

    @property
    def up_to_date(self) -> int:
        """Count of tools that are up to date."""
        return sum(1 for t in self.tools if t.status == ToolStatus.UP_TO_DATE)

    @property
    def not_installed(self) -> int:
        """Count of tools that are not installed."""
        return sum(1 for t in self.tools if t.status == ToolStatus.NOT_INSTALLED)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON output."""
        return {
            "platform": self.platform.value,
            "summary": {
                "updates_available": self.updates_available,
                "up_to_date": self.up_to_date,
                "not_installed": self.not_installed,
            },
            "tools": [t.to_dict() for t in self.tools],
        }
