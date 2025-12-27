"""Rust language plugin for depswiz."""

import re
import tomllib
from pathlib import Path

import httpx

from depswiz.core.logging import get_logger
from depswiz.core.models import LicenseInfo, Package
from depswiz.plugins.base import LanguagePlugin

logger = get_logger("plugins.rust")


class RustPlugin(LanguagePlugin):
    """Plugin for Rust/crates.io ecosystem."""

    @property
    def name(self) -> str:
        return "rust"

    @property
    def display_name(self) -> str:
        return "Rust"

    @property
    def manifest_patterns(self) -> list[str]:
        return ["Cargo.toml"]

    @property
    def lockfile_patterns(self) -> list[str]:
        return ["Cargo.lock"]

    @property
    def ecosystem(self) -> str:
        return "crates.io"

    def detect(self, path: Path) -> bool:
        """Check if this plugin applies to the given path."""
        return (path / "Cargo.toml").exists()

    def parse_manifest(self, path: Path) -> list[Package]:
        """Parse Cargo.toml and extract dependencies."""
        packages = []

        try:
            with open(path, "rb") as f:
                data = tomllib.load(f)

            # Regular dependencies
            for name, spec in data.get("dependencies", {}).items():
                pkg = self._parse_dependency(name, spec, is_dev=False)
                if pkg:
                    packages.append(pkg)

            # Dev dependencies
            for name, spec in data.get("dev-dependencies", {}).items():
                pkg = self._parse_dependency(name, spec, is_dev=True)
                if pkg:
                    packages.append(pkg)

            # Build dependencies
            for name, spec in data.get("build-dependencies", {}).items():
                pkg = self._parse_dependency(name, spec, is_dev=True)
                if pkg:
                    packages.append(pkg)

            # Target-specific dependencies
            for _target, target_deps in data.get("target", {}).items():
                for name, spec in target_deps.get("dependencies", {}).items():
                    pkg = self._parse_dependency(name, spec, is_dev=False)
                    if pkg:
                        packages.append(pkg)

        except tomllib.TOMLDecodeError as e:
            logger.warning("Failed to parse Cargo.toml at %s: %s", path, e)
        except OSError as e:
            logger.warning("Failed to read Cargo.toml at %s: %s", path, e)
        except Exception as e:
            logger.debug("Unexpected error parsing Cargo.toml at %s: %s", path, e)

        return packages

    def _parse_dependency(
        self, name: str, spec: str | dict, is_dev: bool = False
    ) -> Package | None:
        """Parse a Cargo dependency specification."""
        version = None
        constraint = None
        features = None

        if isinstance(spec, str):
            constraint = spec
            version = self._extract_version(spec)
        elif isinstance(spec, dict):
            # Skip path/git dependencies
            if "path" in spec or "git" in spec:
                return None

            version_spec = spec.get("version", "")
            constraint = version_spec
            version = self._extract_version(version_spec)
            features = spec.get("features", [])

        return Package(
            name=name,
            current_version=version,
            constraint=constraint,
            extras=features if features else None,
            is_dev=is_dev,
        )

    def _extract_version(self, constraint: str) -> str | None:
        """Extract version number from a Cargo constraint."""
        # Handle ^ (caret), ~ (tilde), = (exact), >, <, >= , <=
        match = re.search(r"[>=<^~]*\s*(\d+(?:\.\d+)*)", constraint)
        if match:
            return match.group(1)
        return None

    def parse_lockfile(self, path: Path) -> list[Package]:
        """Parse Cargo.lock for resolved versions."""
        packages = []

        try:
            with open(path, "rb") as f:
                data = tomllib.load(f)

            for pkg_data in data.get("package", []):
                name = pkg_data.get("name", "")
                version = pkg_data.get("version", "")
                if name and version:
                    packages.append(Package(name=name, current_version=version))

        except tomllib.TOMLDecodeError as e:
            logger.warning("Failed to parse Cargo.lock at %s: %s", path, e)
        except OSError as e:
            logger.warning("Failed to read Cargo.lock at %s: %s", path, e)
        except Exception as e:
            logger.debug("Unexpected error parsing Cargo.lock at %s: %s", path, e)

        return packages

    async def fetch_latest_version(self, client: httpx.AsyncClient, package: Package) -> str | None:
        """Query crates.io for the latest version."""
        try:
            url = f"https://crates.io/api/v1/crates/{package.name}"
            headers = {"User-Agent": "depswiz/1.0.0"}
            response = await client.get(url, headers=headers)

            if response.status_code == 200:
                data = response.json()
                return data.get("crate", {}).get("max_version")

        except httpx.HTTPStatusError as e:
            logger.debug("HTTP error fetching crates.io info for %s: %s", package.name, e)
        except httpx.RequestError as e:
            logger.debug("Request error fetching crates.io info for %s: %s", package.name, e)
        except Exception as e:
            logger.debug("Unexpected error fetching crates.io info for %s: %s", package.name, e)

        return None

    async def fetch_package_info(self, client: httpx.AsyncClient, package: Package) -> dict | None:
        """Fetch full package information from crates.io."""
        try:
            url = f"https://crates.io/api/v1/crates/{package.name}"
            headers = {"User-Agent": "depswiz/1.0.0"}
            response = await client.get(url, headers=headers)

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
        """Fetch license information from crates.io."""
        try:
            info = await self.fetch_package_info(client, package)
            if info:
                # Get the version-specific info
                versions = info.get("versions", [])
                if versions:
                    # Find the latest version
                    latest = next(
                        (
                            v
                            for v in versions
                            if v.get("num") == info.get("crate", {}).get("max_version")
                        ),
                        versions[0],
                    )
                    license_str = latest.get("license", "")

                    if license_str:
                        # Crates.io uses SPDX expressions directly
                        # Handle "MIT OR Apache-2.0" style
                        if " OR " in license_str or "/" in license_str:
                            # Take the first license
                            first_license = license_str.split(" OR ")[0].split("/")[0].strip()
                            return LicenseInfo.from_spdx(first_license)

                        return LicenseInfo.from_spdx(license_str)

        except Exception as e:
            logger.debug("Error fetching license for %s: %s", package.name, e)

        return None

    def generate_update_command(
        self, packages: list[Package], include_lockfile: bool = True
    ) -> list[str]:
        """Generate Cargo update commands."""
        if not packages:
            return []

        commands = []

        # Update specific packages
        for pkg in packages:
            if pkg.latest_version:
                commands.append(f"cargo update -p {pkg.name} --precise {pkg.latest_version}")
            else:
                commands.append(f"cargo update -p {pkg.name}")

        return commands

    def supports_workspaces(self) -> bool:
        """Cargo supports workspaces."""
        return True

    def detect_workspaces(self, path: Path) -> list[Path]:
        """Find Cargo workspace members."""
        members = []

        try:
            cargo_toml = path / "Cargo.toml"
            if not cargo_toml.exists():
                return []

            with open(cargo_toml, "rb") as f:
                data = tomllib.load(f)

            workspace = data.get("workspace", {})
            member_patterns = workspace.get("members", [])

            for pattern in member_patterns:
                # Handle glob patterns
                if "*" in pattern:
                    for member_path in path.glob(pattern):
                        if (member_path / "Cargo.toml").exists():
                            members.append(member_path)
                else:
                    member_path = path / pattern
                    if (member_path / "Cargo.toml").exists():
                        members.append(member_path)

        except tomllib.TOMLDecodeError as e:
            logger.warning("Failed to parse Cargo.toml for workspaces at %s: %s", path, e)
        except OSError as e:
            logger.warning("Failed to read workspace config at %s: %s", path, e)
        except Exception as e:
            logger.debug("Unexpected error detecting workspaces at %s: %s", path, e)

        return members
