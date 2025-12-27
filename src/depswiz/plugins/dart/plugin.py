"""Dart/Flutter language plugin for depswiz."""

import re
from pathlib import Path

import httpx
import yaml

from depswiz.core.logging import get_logger
from depswiz.core.models import LicenseInfo, Package
from depswiz.plugins.base import LanguagePlugin

logger = get_logger("plugins.dart")


class DartPlugin(LanguagePlugin):
    """Plugin for Dart/Flutter/pub.dev ecosystem."""

    @property
    def name(self) -> str:
        return "dart"

    @property
    def display_name(self) -> str:
        return "Dart/Flutter"

    @property
    def manifest_patterns(self) -> list[str]:
        return ["pubspec.yaml"]

    @property
    def lockfile_patterns(self) -> list[str]:
        return ["pubspec.lock"]

    @property
    def ecosystem(self) -> str:
        return "Pub"

    def detect(self, path: Path) -> bool:
        """Check if this plugin applies to the given path."""
        return (path / "pubspec.yaml").exists()

    def parse_manifest(self, path: Path) -> list[Package]:
        """Parse pubspec.yaml and extract dependencies."""
        packages = []

        try:
            with open(path) as f:
                data = yaml.safe_load(f)

            if not data:
                return []

            # Regular dependencies
            for name, spec in (data.get("dependencies") or {}).items():
                pkg = self._parse_dependency(name, spec, is_dev=False)
                if pkg:
                    packages.append(pkg)

            # Dev dependencies
            for name, spec in (data.get("dev_dependencies") or {}).items():
                pkg = self._parse_dependency(name, spec, is_dev=True)
                if pkg:
                    packages.append(pkg)

            # Dependency overrides (note these, but mark specially)
            for name, spec in (data.get("dependency_overrides") or {}).items():
                pkg = self._parse_dependency(name, spec, is_dev=False)
                if pkg:
                    packages.append(pkg)

        except yaml.YAMLError as e:
            logger.warning("Failed to parse pubspec.yaml at %s: %s", path, e)
        except OSError as e:
            logger.warning("Failed to read pubspec.yaml at %s: %s", path, e)
        except Exception as e:
            logger.debug("Unexpected error parsing pubspec.yaml at %s: %s", path, e)

        return packages

    def _parse_dependency(self, name: str, spec, is_dev: bool = False) -> Package | None:
        """Parse a pub dependency specification."""
        # Skip SDK dependencies (flutter, flutter_test)
        if name in ("flutter", "flutter_test", "flutter_localizations", "flutter_driver"):
            return None

        version = None
        constraint = None

        if spec is None:
            # Bare dependency, any version
            constraint = "any"
        elif isinstance(spec, str):
            constraint = spec
            version = self._extract_version(spec)
        elif isinstance(spec, dict):
            # Skip path, git, sdk dependencies
            if "path" in spec or "git" in spec or "sdk" in spec:
                return None

            version_spec = spec.get("version")
            if version_spec:
                constraint = version_spec
                version = self._extract_version(version_spec)
            else:
                # Hosted dependency without version
                constraint = "any"

        return Package(
            name=name,
            current_version=version,
            constraint=constraint,
            is_dev=is_dev,
        )

    def _extract_version(self, constraint: str) -> str | None:
        """Extract version number from a pub constraint."""
        if not constraint:
            return None

        # Handle ^ (caret), >= , <=, >, <, any
        if constraint == "any":
            return None

        match = re.search(r"[>=<^]*\s*(\d+\.\d+\.\d+(?:[+-][a-zA-Z0-9.]+)?)", constraint)
        if match:
            return match.group(1)

        return None

    def parse_lockfile(self, path: Path) -> list[Package]:
        """Parse pubspec.lock for resolved versions."""
        packages = []

        try:
            with open(path) as f:
                data = yaml.safe_load(f)

            if not data:
                return []

            for name, pkg_data in (data.get("packages") or {}).items():
                # Skip SDK packages
                source = pkg_data.get("source", "")
                if source == "sdk":
                    continue

                version = pkg_data.get("version", "")
                if name and version:
                    packages.append(Package(name=name, current_version=version))

        except yaml.YAMLError as e:
            logger.warning("Failed to parse pubspec.lock at %s: %s", path, e)
        except OSError as e:
            logger.warning("Failed to read pubspec.lock at %s: %s", path, e)
        except Exception as e:
            logger.debug("Unexpected error parsing pubspec.lock at %s: %s", path, e)

        return packages

    async def fetch_latest_version(self, client: httpx.AsyncClient, package: Package) -> str | None:
        """Query pub.dev for the latest version."""
        try:
            url = f"https://pub.dev/api/packages/{package.name}"
            response = await client.get(url)

            if response.status_code == 200:
                data = response.json()
                return data.get("latest", {}).get("version")

        except httpx.HTTPStatusError as e:
            logger.debug("HTTP error fetching pub.dev info for %s: %s", package.name, e)
        except httpx.RequestError as e:
            logger.debug("Request error fetching pub.dev info for %s: %s", package.name, e)
        except Exception as e:
            logger.debug("Unexpected error fetching pub.dev info for %s: %s", package.name, e)

        return None

    async def fetch_package_info(self, client: httpx.AsyncClient, package: Package) -> dict | None:
        """Fetch full package information from pub.dev."""
        try:
            url = f"https://pub.dev/api/packages/{package.name}"
            response = await client.get(url)

            if response.status_code == 200:
                return response.json()

        except httpx.HTTPStatusError as e:
            logger.debug("HTTP error fetching package info for %s: %s", package.name, e)
        except httpx.RequestError as e:
            logger.debug("Request error fetching package info for %s: %s", package.name, e)
        except Exception as e:
            logger.debug("Unexpected error fetching package info for %s: %s", package.name, e)

        return None

    async def fetch_license(
        self, client: httpx.AsyncClient, package: Package
    ) -> LicenseInfo | None:
        """Fetch license information from pub.dev."""
        try:
            info = await self.fetch_package_info(client, package)
            if info:
                latest = info.get("latest", {})
                latest.get("pubspec", {})

                # Check for license in pubspec
                # Note: pub.dev doesn't have a direct license field in API
                # We'd need to check the package's LICENSE file

                # Try to get from the score card
                url = f"https://pub.dev/api/packages/{package.name}/score"
                response = await client.get(url)

                if response.status_code == 200:
                    score_data = response.json()
                    # Score data might contain license info
                    tags = score_data.get("tags", [])
                    for tag in tags:
                        if tag.startswith("license:"):
                            license_id = tag.split(":")[-1]
                            return LicenseInfo.from_spdx(license_id.upper())

        except Exception as e:
            logger.debug("Error fetching license for %s: %s", package.name, e)

        return None

    def generate_update_command(
        self, packages: list[Package], include_lockfile: bool = True
    ) -> list[str]:
        """Generate pub/flutter update commands."""
        if not packages:
            return []

        commands = []

        # Determine if this is a Flutter project
        is_flutter = Path("pubspec.yaml").exists() and self._is_flutter_project()

        if is_flutter:
            # Flutter project
            commands.append("flutter pub upgrade")
            if include_lockfile:
                commands.append("flutter pub get")
        else:
            # Pure Dart project
            commands.append("dart pub upgrade")
            if include_lockfile:
                commands.append("dart pub get")

        return commands

    def _is_flutter_project(self) -> bool:
        """Check if the current project is a Flutter project."""
        try:
            with open("pubspec.yaml") as f:
                data = yaml.safe_load(f)

            if not data:
                return False

            # Check for flutter SDK dependency
            deps = data.get("dependencies", {})
            if "flutter" in deps:
                return True

            # Check for flutter in environment
            env = data.get("environment", {})
            if "flutter" in env:
                return True

        except yaml.YAMLError as e:
            logger.debug("Failed to parse pubspec.yaml for Flutter detection: %s", e)
        except OSError as e:
            logger.debug("Failed to read pubspec.yaml for Flutter detection: %s", e)
        except Exception as e:
            logger.debug("Unexpected error checking Flutter project: %s", e)

        return False

    def supports_workspaces(self) -> bool:
        """Dart/Flutter supports melos workspaces."""
        return True

    def detect_workspaces(self, path: Path) -> list[Path]:
        """Find Dart workspace members (melos style)."""
        members = []

        try:
            # Check for melos.yaml
            melos_yaml = path / "melos.yaml"
            if melos_yaml.exists():
                with open(melos_yaml) as f:
                    data = yaml.safe_load(f)

                packages_patterns = data.get("packages", [])
                for pattern in packages_patterns:
                    for member_path in path.glob(pattern):
                        if (member_path / "pubspec.yaml").exists():
                            members.append(member_path)

            # Also check for pub workspace (Dart 3.5+)
            pubspec = path / "pubspec.yaml"
            if pubspec.exists():
                with open(pubspec) as f:
                    data = yaml.safe_load(f)

                workspace = data.get("workspace", [])
                for member in workspace:
                    member_path = path / member
                    if (member_path / "pubspec.yaml").exists():
                        members.append(member_path)

        except yaml.YAMLError as e:
            logger.warning("Failed to parse workspace config at %s: %s", path, e)
        except OSError as e:
            logger.warning("Failed to read workspace config at %s: %s", path, e)
        except Exception as e:
            logger.debug("Unexpected error detecting workspaces at %s: %s", path, e)

        return members
