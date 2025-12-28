"""Go language plugin for depswiz."""

import re
from pathlib import Path

import httpx

from depswiz.core.logging import get_logger
from depswiz.core.models import LicenseInfo, Package
from depswiz.plugins.base import LanguagePlugin

logger = get_logger("plugins.golang")


class GoPlugin(LanguagePlugin):
    """Plugin for Go modules ecosystem."""

    @property
    def name(self) -> str:
        return "golang"

    @property
    def display_name(self) -> str:
        return "Go"

    @property
    def manifest_patterns(self) -> list[str]:
        return ["go.mod"]

    @property
    def lockfile_patterns(self) -> list[str]:
        return ["go.sum"]

    @property
    def ecosystem(self) -> str:
        return "Go"

    def detect(self, path: Path) -> bool:
        """Check if this plugin applies to the given path."""
        return (path / "go.mod").exists()

    def parse_manifest(self, path: Path) -> list[Package]:
        """Parse go.mod and extract dependencies."""
        packages = []

        try:
            content = path.read_text()

            # Track if we're in a require block
            in_require_block = False

            for line in content.split("\n"):
                line = line.strip()

                # Skip comments and empty lines
                if not line or line.startswith("//"):
                    continue

                # Handle require block start/end
                if line.startswith("require ("):
                    in_require_block = True
                    continue
                elif line == ")":
                    in_require_block = False
                    continue

                # Handle single-line require
                if line.startswith("require ") and "(" not in line:
                    # require github.com/foo/bar v1.2.3
                    match = re.match(r'require\s+(\S+)\s+v?([\d.]+\S*)', line)
                    if match:
                        pkg = self._create_package(match.group(1), match.group(2))
                        if pkg:
                            packages.append(pkg)
                    continue

                # Handle dependencies inside require block
                if in_require_block:
                    # github.com/foo/bar v1.2.3
                    match = re.match(r'(\S+)\s+v?([\d.]+\S*)', line)
                    if match:
                        pkg = self._create_package(match.group(1), match.group(2))
                        if pkg:
                            packages.append(pkg)

        except OSError as e:
            logger.warning("Failed to read go.mod at %s: %s", path, e)
        except Exception as e:
            logger.debug("Unexpected error parsing go.mod at %s: %s", path, e)

        return packages

    def _create_package(self, module_path: str, version: str) -> Package | None:
        """Create a Package from module path and version."""
        # Skip indirect dependencies (they have // indirect comment)
        if "// indirect" in version:
            version = version.split("//")[0].strip()

        # Clean up version (remove +incompatible suffix, etc.)
        clean_version = version.replace("+incompatible", "").strip()

        return Package(
            name=module_path,
            current_version=clean_version,
            constraint=f"v{clean_version}" if not clean_version.startswith("v") else clean_version,
            is_dev=False,
        )

    def parse_lockfile(self, path: Path) -> list[Package]:
        """Parse go.sum for resolved versions.

        Note: go.sum contains checksums, not just versions. Each module
        may have multiple entries (for the module and its go.mod file).
        We deduplicate and extract unique module versions.
        """
        packages = []
        seen: set[tuple[str, str]] = set()

        try:
            content = path.read_text()

            for line in content.split("\n"):
                line = line.strip()
                if not line:
                    continue

                # Format: module/path v1.2.3 h1:checksum
                # or: module/path v1.2.3/go.mod h1:checksum
                parts = line.split()
                if len(parts) >= 2:
                    module_path = parts[0]
                    version = parts[1]

                    # Skip go.mod entries (duplicates)
                    if version.endswith("/go.mod"):
                        continue

                    # Clean version
                    clean_version = version.lstrip("v").replace("+incompatible", "")

                    key = (module_path, clean_version)
                    if key not in seen:
                        seen.add(key)
                        packages.append(Package(
                            name=module_path,
                            current_version=clean_version,
                        ))

        except OSError as e:
            logger.warning("Failed to read go.sum at %s: %s", path, e)
        except Exception as e:
            logger.debug("Unexpected error parsing go.sum at %s: %s", path, e)

        return packages

    async def fetch_latest_version(self, client: httpx.AsyncClient, package: Package) -> str | None:
        """Query Go module proxy for the latest version."""
        try:
            # Use the Go module proxy
            # Note: module paths with capital letters need to be escaped
            escaped_path = self._escape_module_path(package.name)
            url = f"https://proxy.golang.org/{escaped_path}/@latest"

            response = await client.get(url, timeout=30.0)

            if response.status_code == 200:
                data = response.json()
                version = data.get("Version", "")
                # Strip 'v' prefix for consistency
                return version.lstrip("v")

            # Try list endpoint as fallback
            list_url = f"https://proxy.golang.org/{escaped_path}/@v/list"
            response = await client.get(list_url, timeout=30.0)

            if response.status_code == 200:
                versions = response.text.strip().split("\n")
                if versions and versions[-1]:
                    return versions[-1].lstrip("v")

        except httpx.HTTPStatusError as e:
            logger.debug("HTTP error fetching Go module info for %s: %s", package.name, e)
        except httpx.RequestError as e:
            logger.debug("Request error fetching Go module info for %s: %s", package.name, e)
        except Exception as e:
            logger.debug("Unexpected error fetching Go module info for %s: %s", package.name, e)

        return None

    def _escape_module_path(self, path: str) -> str:
        """Escape module path for Go module proxy.

        Capital letters in module paths are escaped as !lowercase.
        """
        result = []
        for char in path:
            if char.isupper():
                result.append("!")
                result.append(char.lower())
            else:
                result.append(char)
        return "".join(result)

    async def fetch_package_info(self, client: httpx.AsyncClient, package: Package) -> dict | None:
        """Fetch full package information from Go module proxy."""
        try:
            escaped_path = self._escape_module_path(package.name)
            url = f"https://proxy.golang.org/{escaped_path}/@latest"

            response = await client.get(url, timeout=30.0)

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
        """Fetch license information from pkg.go.dev.

        Note: Go module proxy doesn't provide license info directly.
        We use pkg.go.dev API as a fallback.
        """
        try:
            # Try to get license from pkg.go.dev
            url = f"https://pkg.go.dev/{package.name}?tab=licenses"
            response = await client.get(url, timeout=30.0, follow_redirects=True)

            if response.status_code == 200:
                content = response.text

                # Look for common license identifiers in the page
                license_patterns = [
                    (r'MIT License', 'MIT'),
                    (r'Apache License.*2\.0', 'Apache-2.0'),
                    (r'BSD-3-Clause', 'BSD-3-Clause'),
                    (r'BSD-2-Clause', 'BSD-2-Clause'),
                    (r'ISC License', 'ISC'),
                    (r'MPL-2\.0', 'MPL-2.0'),
                    (r'GPL-3\.0', 'GPL-3.0-only'),
                    (r'GPL-2\.0', 'GPL-2.0-only'),
                    (r'LGPL-3\.0', 'LGPL-3.0-only'),
                    (r'Unlicense', 'Unlicense'),
                ]

                for pattern, spdx_id in license_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        return LicenseInfo.from_spdx(spdx_id)

        except Exception as e:
            logger.debug("Error fetching license for %s: %s", package.name, e)

        return None

    def generate_update_command(
        self, packages: list[Package], include_lockfile: bool = True
    ) -> list[str]:
        """Generate Go update commands."""
        if not packages:
            return []

        commands = []

        # Update specific packages
        for pkg in packages:
            if pkg.latest_version:
                version = pkg.latest_version
                if not version.startswith("v"):
                    version = f"v{version}"
                commands.append(f"go get {pkg.name}@{version}")
            else:
                commands.append(f"go get -u {pkg.name}")

        # Tidy up after updates
        if include_lockfile:
            commands.append("go mod tidy")

        return commands

    def supports_workspaces(self) -> bool:
        """Go supports workspaces (go.work)."""
        return True

    def detect_workspaces(self, path: Path) -> list[Path]:
        """Find Go workspace members."""
        members = []

        try:
            go_work = path / "go.work"
            if not go_work.exists():
                return []

            content = go_work.read_text()
            in_use_block = False

            for line in content.split("\n"):
                line = line.strip()

                # Skip comments and empty lines
                if not line or line.startswith("//"):
                    continue

                # Handle use block start/end
                if line.startswith("use ("):
                    in_use_block = True
                    continue
                elif line == ")":
                    in_use_block = False
                    continue

                # Handle single-line use
                if line.startswith("use ") and "(" not in line:
                    member_path = line.replace("use ", "").strip()
                    resolved = path / member_path
                    if resolved.exists() and (resolved / "go.mod").exists():
                        members.append(resolved)
                    continue

                # Handle paths inside use block
                if in_use_block:
                    member_path = line.strip()
                    if member_path:
                        resolved = path / member_path
                        if resolved.exists() and (resolved / "go.mod").exists():
                            members.append(resolved)

        except OSError as e:
            logger.warning("Failed to read go.work for workspaces at %s: %s", path, e)
        except Exception as e:
            logger.debug("Unexpected error detecting workspaces at %s: %s", path, e)

        return members
