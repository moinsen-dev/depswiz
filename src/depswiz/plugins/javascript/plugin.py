"""JavaScript/TypeScript language plugin for depswiz."""

import json
import re
from pathlib import Path

import httpx

from depswiz.core.logging import get_logger
from depswiz.core.models import LicenseInfo, Package
from depswiz.plugins.base import LanguagePlugin

logger = get_logger("plugins.javascript")


class JavaScriptPlugin(LanguagePlugin):
    """Plugin for JavaScript/TypeScript/npm ecosystem."""

    @property
    def name(self) -> str:
        return "javascript"

    @property
    def display_name(self) -> str:
        return "JavaScript/TypeScript"

    @property
    def manifest_patterns(self) -> list[str]:
        return ["package.json"]

    @property
    def lockfile_patterns(self) -> list[str]:
        return ["package-lock.json", "yarn.lock", "pnpm-lock.yaml"]

    @property
    def ecosystem(self) -> str:
        return "npm"

    def detect(self, path: Path) -> bool:
        """Check if this plugin applies to the given path."""
        return (path / "package.json").exists()

    def parse_manifest(self, path: Path) -> list[Package]:
        """Parse package.json and extract dependencies."""
        packages = []

        try:
            with open(path) as f:
                data = json.load(f)

            # Regular dependencies
            for name, version in (data.get("dependencies") or {}).items():
                pkg = self._parse_dependency(name, version, is_dev=False)
                if pkg:
                    packages.append(pkg)

            # Dev dependencies
            for name, version in (data.get("devDependencies") or {}).items():
                pkg = self._parse_dependency(name, version, is_dev=True)
                if pkg:
                    packages.append(pkg)

            # Peer dependencies
            for name, version in (data.get("peerDependencies") or {}).items():
                pkg = self._parse_dependency(name, version, is_dev=False)
                if pkg:
                    packages.append(pkg)

            # Optional dependencies
            for name, version in (data.get("optionalDependencies") or {}).items():
                pkg = self._parse_dependency(name, version, is_dev=False)
                if pkg:
                    packages.append(pkg)

        except json.JSONDecodeError as e:
            logger.warning("Failed to parse package.json at %s: %s", path, e)
        except OSError as e:
            logger.warning("Failed to read package.json at %s: %s", path, e)
        except Exception as e:
            logger.debug("Unexpected error parsing package.json at %s: %s", path, e)

        return packages

    def _parse_dependency(self, name: str, version: str, is_dev: bool = False) -> Package | None:
        """Parse an npm dependency specification."""
        # Skip file:, link:, git:, github: dependencies
        if any(
            version.startswith(p)
            for p in ("file:", "link:", "git:", "git+", "github:", "http:", "https:")
        ):
            return None

        # Handle npm: protocol
        if version.startswith("npm:"):
            version = version[4:]

        constraint = version
        current_version = self._extract_version(version)

        return Package(
            name=name,
            current_version=current_version,
            constraint=constraint,
            is_dev=is_dev,
        )

    def _extract_version(self, constraint: str) -> str | None:
        """Extract version number from an npm constraint."""
        if not constraint:
            return None

        # Handle workspace protocol
        if constraint.startswith("workspace:"):
            return None

        # Handle * or latest
        if constraint in ("*", "latest", "next"):
            return None

        # Handle ^ (caret), ~ (tilde), >= , <=, >, <, =, x ranges
        match = re.search(r"[>=<^~]*\s*v?(\d+(?:\.\d+)*(?:-[a-zA-Z0-9.]+)?)", constraint)
        if match:
            return match.group(1)

        return None

    def parse_lockfile(self, path: Path) -> list[Package]:
        """Parse lockfile for resolved versions."""
        if path.name == "package-lock.json":
            return self._parse_package_lock(path)
        elif path.name == "yarn.lock":
            return self._parse_yarn_lock(path)
        elif path.name == "pnpm-lock.yaml":
            return self._parse_pnpm_lock(path)
        return []

    def _parse_package_lock(self, path: Path) -> list[Package]:
        """Parse package-lock.json."""
        packages = []

        try:
            with open(path) as f:
                data = json.load(f)

            # v2/v3 format
            for name, pkg_data in (data.get("packages") or {}).items():
                if not name or name == "":
                    continue

                # Extract package name from path (e.g., "node_modules/lodash")
                pkg_name = name.split("node_modules/")[-1]

                # Handle scoped packages
                if pkg_name.startswith("@"):
                    parts = pkg_name.split("/")
                    if len(parts) >= 2:
                        pkg_name = f"{parts[0]}/{parts[1]}"

                version = pkg_data.get("version", "")
                if pkg_name and version and "/" not in pkg_name[1:]:
                    packages.append(Package(name=pkg_name, current_version=version))

        except json.JSONDecodeError as e:
            logger.warning("Failed to parse package-lock.json at %s: %s", path, e)
        except OSError as e:
            logger.warning("Failed to read package-lock.json at %s: %s", path, e)
        except Exception as e:
            logger.debug("Unexpected error parsing package-lock.json at %s: %s", path, e)

        return packages

    def _parse_yarn_lock(self, path: Path) -> list[Package]:
        """Parse yarn.lock (v1 format)."""
        packages = []

        try:
            content = path.read_text()

            # Simple parsing of yarn.lock v1 format
            current_name = None
            for line in content.splitlines():
                line = line.rstrip()

                # Package header line
                if not line.startswith(" ") and line and not line.startswith("#"):
                    # Extract package name
                    match = re.match(r'^"?(@?[^@"]+)@', line)
                    if match:
                        current_name = match.group(1)

                # Version line
                elif line.strip().startswith("version "):
                    version_match = re.search(r'version\s+"?([^"]+)"?', line)
                    if version_match and current_name:
                        packages.append(
                            Package(name=current_name, current_version=version_match.group(1))
                        )
                        current_name = None

        except OSError as e:
            logger.warning("Failed to read yarn.lock at %s: %s", path, e)
        except Exception as e:
            logger.debug("Unexpected error parsing yarn.lock at %s: %s", path, e)

        return packages

    def _parse_pnpm_lock(self, path: Path) -> list[Package]:
        """Parse pnpm-lock.yaml."""
        packages = []

        try:
            import yaml

            with open(path) as f:
                data = yaml.safe_load(f)

            if not data:
                return []

            # v6+ format
            for pkg_path, _pkg_data in (data.get("packages") or {}).items():
                # Parse package path like "/lodash@4.17.21"
                match = re.match(r"^/(@?[^@]+)@([^(@]+)", pkg_path)
                if match:
                    name = match.group(1)
                    version = match.group(2)
                    packages.append(Package(name=name, current_version=version))

        except yaml.YAMLError as e:
            logger.warning("Failed to parse pnpm-lock.yaml at %s: %s", path, e)
        except OSError as e:
            logger.warning("Failed to read pnpm-lock.yaml at %s: %s", path, e)
        except Exception as e:
            logger.debug("Unexpected error parsing pnpm-lock.yaml at %s: %s", path, e)

        return packages

    async def fetch_latest_version(self, client: httpx.AsyncClient, package: Package) -> str | None:
        """Query npm registry for the latest version."""
        try:
            # Handle scoped packages
            encoded_name = package.name.replace("/", "%2F")
            url = f"https://registry.npmjs.org/{encoded_name}"
            response = await client.get(url)

            if response.status_code == 200:
                data = response.json()
                return data.get("dist-tags", {}).get("latest")

        except httpx.HTTPStatusError as e:
            logger.debug("HTTP error fetching npm info for %s: %s", package.name, e)
        except httpx.RequestError as e:
            logger.debug("Request error fetching npm info for %s: %s", package.name, e)
        except Exception as e:
            logger.debug("Unexpected error fetching npm info for %s: %s", package.name, e)

        return None

    async def fetch_package_info(self, client: httpx.AsyncClient, package: Package) -> dict | None:
        """Fetch full package information from npm registry."""
        try:
            encoded_name = package.name.replace("/", "%2F")
            url = f"https://registry.npmjs.org/{encoded_name}"
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
        """Fetch license information from npm registry."""
        try:
            info = await self.fetch_package_info(client, package)
            if info:
                # Get latest version info
                latest_version = info.get("dist-tags", {}).get("latest")
                versions = info.get("versions", {})

                version_info = versions.get(latest_version, {})
                license_data = version_info.get("license")

                if license_data:
                    if isinstance(license_data, str):
                        return LicenseInfo.from_spdx(license_data)
                    elif isinstance(license_data, dict):
                        # Handle older { "type": "MIT" } format
                        license_type = license_data.get("type", "")
                        return LicenseInfo.from_spdx(license_type)

        except Exception as e:
            logger.debug("Error fetching license for %s: %s", package.name, e)

        return None

    def generate_update_command(
        self, packages: list[Package], include_lockfile: bool = True
    ) -> list[str]:
        """Generate npm/yarn/pnpm update commands."""
        if not packages:
            return []

        commands = []
        package_specs = [
            f"{pkg.name}@{pkg.latest_version}" if pkg.latest_version else pkg.name
            for pkg in packages
        ]

        # Detect package manager
        if Path("pnpm-lock.yaml").exists():
            # pnpm
            commands.append(f"pnpm update {' '.join(package_specs)}")
        elif Path("yarn.lock").exists():
            # yarn
            commands.append(f"yarn upgrade {' '.join(package_specs)}")
        else:
            # npm
            commands.append(f"npm update {' '.join(package_specs)}")

        return commands

    def supports_workspaces(self) -> bool:
        """npm/yarn/pnpm support workspaces."""
        return True

    def detect_workspaces(self, path: Path) -> list[Path]:
        """Find npm/yarn/pnpm workspace members."""
        members = []

        try:
            package_json = path / "package.json"
            if not package_json.exists():
                return []

            with open(package_json) as f:
                data = json.load(f)

            workspaces = data.get("workspaces", [])

            # Handle yarn workspaces format
            if isinstance(workspaces, dict):
                workspaces = workspaces.get("packages", [])

            for pattern in workspaces:
                # Handle glob patterns
                for member_path in path.glob(pattern):
                    if (member_path / "package.json").exists():
                        members.append(member_path)

            # Also check for pnpm-workspace.yaml
            pnpm_workspace = path / "pnpm-workspace.yaml"
            if pnpm_workspace.exists():
                import yaml

                with open(pnpm_workspace) as f:
                    pnpm_data = yaml.safe_load(f)

                for pattern in pnpm_data.get("packages", []):
                    for member_path in path.glob(pattern):
                        if (member_path / "package.json").exists():
                            members.append(member_path)

        except json.JSONDecodeError as e:
            logger.warning("Failed to parse package.json for workspaces at %s: %s", path, e)
        except yaml.YAMLError as e:
            logger.warning("Failed to parse pnpm-workspace.yaml at %s: %s", path, e)
        except OSError as e:
            logger.warning("Failed to read workspace config at %s: %s", path, e)
        except Exception as e:
            logger.debug("Unexpected error detecting workspaces at %s: %s", path, e)

        return list(set(members))  # Deduplicate
