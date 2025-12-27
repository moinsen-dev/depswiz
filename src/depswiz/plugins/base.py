"""Base plugin class for language support."""

from abc import ABC, abstractmethod
from pathlib import Path

import httpx

from depswiz.core.models import LicenseInfo, Package


class LanguagePlugin(ABC):
    """Abstract base class for language plugins.

    Each language plugin implements support for a specific ecosystem
    (Python/PyPI, Rust/crates.io, Dart/pub.dev, JavaScript/npm).

    To create a new plugin:
    1. Subclass LanguagePlugin
    2. Implement all abstract methods
    3. Register via entry_points in pyproject.toml
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique plugin identifier (e.g., 'python', 'rust').

        This is used for plugin discovery and configuration.
        """

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable name for output (e.g., 'Python', 'Rust')."""

    @property
    @abstractmethod
    def manifest_patterns(self) -> list[str]:
        """Glob patterns for manifest files.

        Examples: ["pyproject.toml"], ["Cargo.toml"], ["package.json"]
        """

    @property
    @abstractmethod
    def lockfile_patterns(self) -> list[str]:
        """Glob patterns for lockfile files.

        Examples: ["uv.lock", "poetry.lock"], ["Cargo.lock"], ["package-lock.json"]
        """

    @property
    def ecosystem(self) -> str:
        """OSV ecosystem identifier for vulnerability queries.

        Override if different from the plugin name.
        Common values: "PyPI", "crates.io", "npm", "Pub"
        """
        return self.name.capitalize()

    @abstractmethod
    def detect(self, path: Path) -> bool:
        """Check if this plugin applies to the given path.

        Args:
            path: Directory path to check

        Returns:
            True if any manifest files are found
        """

    @abstractmethod
    def parse_manifest(self, path: Path) -> list[Package]:
        """Parse manifest file and extract dependencies.

        Args:
            path: Path to the manifest file

        Returns:
            List of Package objects with name, constraint, and is_dev fields
        """

    @abstractmethod
    def parse_lockfile(self, path: Path) -> list[Package]:
        """Parse lockfile for resolved versions.

        Args:
            path: Path to the lockfile

        Returns:
            List of Package objects with name and current_version fields
        """

    @abstractmethod
    async def fetch_latest_version(self, client: httpx.AsyncClient, package: Package) -> str | None:
        """Query registry for the latest version of a package.

        Args:
            client: Async HTTP client
            package: Package to look up

        Returns:
            Latest version string, or None if not found
        """

    @abstractmethod
    async def fetch_package_info(self, client: httpx.AsyncClient, package: Package) -> dict | None:
        """Fetch full package information from registry.

        Args:
            client: Async HTTP client
            package: Package to look up

        Returns:
            Raw package info dict from registry, or None if not found
        """

    @abstractmethod
    async def fetch_license(
        self, client: httpx.AsyncClient, package: Package
    ) -> LicenseInfo | None:
        """Fetch license information from registry.

        Args:
            client: Async HTTP client
            package: Package to look up

        Returns:
            LicenseInfo object, or None if not found
        """

    @abstractmethod
    def generate_update_command(
        self, packages: list[Package], include_lockfile: bool = True
    ) -> list[str]:
        """Generate native update commands for the ecosystem.

        Args:
            packages: List of packages to update
            include_lockfile: Whether to include lockfile update command

        Returns:
            List of shell commands to execute
        """

    def supports_workspaces(self) -> bool:
        """Whether this plugin supports workspace/monorepo detection.

        Override and return True if your plugin can detect workspaces.
        """
        return False

    def detect_workspaces(self, path: Path) -> list[Path]:
        """Find workspace member paths.

        Args:
            path: Root path to search from

        Returns:
            List of paths to workspace member directories
        """
        return []

    def find_manifest_files(self, path: Path, recursive: bool = False) -> list[Path]:
        """Find all manifest files in the given path.

        Args:
            path: Directory to search
            recursive: Whether to search subdirectories

        Returns:
            List of manifest file paths
        """
        found: list[Path] = []
        for pattern in self.manifest_patterns:
            if recursive:
                found.extend(path.rglob(pattern))
            else:
                found.extend(path.glob(pattern))
        return sorted(set(found))

    def find_lockfiles(self, path: Path) -> list[Path]:
        """Find all lockfiles in the given path.

        Args:
            path: Directory to search

        Returns:
            List of lockfile paths
        """
        found: list[Path] = []
        for pattern in self.lockfile_patterns:
            found.extend(path.glob(pattern))
        return sorted(set(found))
