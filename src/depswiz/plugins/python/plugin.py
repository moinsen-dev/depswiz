"""Python language plugin for depswiz."""

import re
import tomllib
from pathlib import Path

import httpx

from depswiz.core.logging import get_logger
from depswiz.core.models import LicenseInfo, Package
from depswiz.plugins.base import LanguagePlugin

logger = get_logger("plugins.python")


class PythonPlugin(LanguagePlugin):
    """Plugin for Python/PyPI ecosystem."""

    @property
    def name(self) -> str:
        return "python"

    @property
    def display_name(self) -> str:
        return "Python"

    @property
    def manifest_patterns(self) -> list[str]:
        return ["pyproject.toml", "requirements.txt", "requirements*.txt", "setup.py"]

    @property
    def lockfile_patterns(self) -> list[str]:
        return ["uv.lock", "poetry.lock", "Pipfile.lock", "requirements.lock"]

    @property
    def ecosystem(self) -> str:
        return "PyPI"

    def detect(self, path: Path) -> bool:
        """Check if this plugin applies to the given path."""
        for pattern in self.manifest_patterns:
            if list(path.glob(pattern)):
                return True
        return False

    def parse_manifest(self, path: Path) -> list[Package]:
        """Parse manifest file and extract dependencies."""
        if path.name == "pyproject.toml":
            return self._parse_pyproject_toml(path)
        elif path.name.startswith("requirements"):
            return self._parse_requirements_txt(path)
        elif path.name == "setup.py":
            return self._parse_setup_py(path)
        return []

    def _parse_pyproject_toml(self, path: Path) -> list[Package]:
        """Parse pyproject.toml for dependencies."""
        packages = []

        try:
            with open(path, "rb") as f:
                data = tomllib.load(f)

            # PEP 621 style dependencies
            project = data.get("project", {})
            deps = project.get("dependencies", [])
            for dep in deps:
                pkg = self._parse_requirement_string(dep, is_dev=False)
                if pkg:
                    packages.append(pkg)

            # Optional dependencies (often dev deps)
            optional_deps = project.get("optional-dependencies", {})
            for group, deps in optional_deps.items():
                is_dev = group in ("dev", "test", "testing", "development")
                for dep in deps:
                    pkg = self._parse_requirement_string(dep, is_dev=is_dev)
                    if pkg:
                        packages.append(pkg)

            # Poetry style
            poetry = data.get("tool", {}).get("poetry", {})
            if poetry:
                for dep, version in poetry.get("dependencies", {}).items():
                    if dep.lower() == "python":
                        continue
                    pkg = self._parse_poetry_dependency(dep, version, is_dev=False)
                    if pkg:
                        packages.append(pkg)

                for dep, version in poetry.get("dev-dependencies", {}).items():
                    pkg = self._parse_poetry_dependency(dep, version, is_dev=True)
                    if pkg:
                        packages.append(pkg)

                # Poetry groups
                for group_name, group_data in poetry.get("group", {}).items():
                    is_dev = group_name in ("dev", "test", "development")
                    for dep, version in group_data.get("dependencies", {}).items():
                        pkg = self._parse_poetry_dependency(dep, version, is_dev=is_dev)
                        if pkg:
                            packages.append(pkg)

        except tomllib.TOMLDecodeError as e:
            logger.warning("Failed to parse pyproject.toml at %s: %s", path, e)
        except OSError as e:
            logger.warning("Failed to read pyproject.toml at %s: %s", path, e)
        except Exception as e:
            logger.debug("Unexpected error parsing pyproject.toml at %s: %s", path, e)

        return packages

    def _parse_requirement_string(self, req: str, is_dev: bool = False) -> Package | None:
        """Parse a PEP 508 requirement string."""
        # Pattern to match package name, extras, and version constraint
        pattern = r"^([a-zA-Z0-9][-a-zA-Z0-9._]*)(\[[^\]]+\])?\s*(.*)$"
        match = re.match(pattern, req.strip())

        if not match:
            return None

        name = match.group(1)
        extras_str = match.group(2)
        constraint = match.group(3).strip() if match.group(3) else None

        # Remove environment markers (e.g., ; python_version < "3.10")
        if constraint and ";" in constraint:
            constraint = constraint.split(";")[0].strip()

        extras = None
        if extras_str:
            extras = [e.strip() for e in extras_str[1:-1].split(",")]

        # Extract version from constraint
        version = None
        if constraint:
            # Try to extract the minimum version from >= or ==
            version_match = re.search(r"[>=<~^!]*\s*(\d+\.\d+[\.\d]*)", constraint)
            if version_match:
                version = version_match.group(1)

        return Package(
            name=name,
            current_version=version,
            constraint=constraint or None,
            extras=extras,
            is_dev=is_dev,
        )

    def _parse_poetry_dependency(
        self, name: str, version_spec: str | dict, is_dev: bool = False
    ) -> Package | None:
        """Parse a Poetry-style dependency."""
        if isinstance(version_spec, dict):
            version = version_spec.get("version", "")
            extras = version_spec.get("extras", [])
        else:
            version = version_spec
            extras = None

        # Parse version constraint
        constraint = version if version else None
        current_version = None

        if constraint:
            # Extract version number from constraint
            version_match = re.search(r"[>=<~^]*\s*(\d+\.\d+[\.\d]*)", str(constraint))
            if version_match:
                current_version = version_match.group(1)

        return Package(
            name=name,
            current_version=current_version,
            constraint=str(constraint) if constraint else None,
            extras=extras if extras else None,
            is_dev=is_dev,
        )

    def _parse_requirements_txt(self, path: Path) -> list[Package]:
        """Parse requirements.txt file."""
        packages = []

        try:
            content = path.read_text()
            is_dev = "dev" in path.name.lower() or "test" in path.name.lower()

            for line in content.splitlines():
                line = line.strip()

                # Skip comments and empty lines
                if not line or line.startswith("#") or line.startswith("-"):
                    continue

                pkg = self._parse_requirement_string(line, is_dev=is_dev)
                if pkg:
                    packages.append(pkg)

        except OSError as e:
            logger.warning("Failed to read requirements file at %s: %s", path, e)
        except Exception as e:
            logger.debug("Unexpected error parsing requirements at %s: %s", path, e)

        return packages

    def _parse_setup_py(self, path: Path) -> list[Package]:
        """Parse setup.py for dependencies (basic parsing)."""
        packages = []

        try:
            content = path.read_text()

            # Look for install_requires
            install_match = re.search(r"install_requires\s*=\s*\[(.*?)\]", content, re.DOTALL)
            if install_match:
                deps_str = install_match.group(1)
                for dep in re.findall(r'["\']([^"\']+)["\']', deps_str):
                    pkg = self._parse_requirement_string(dep, is_dev=False)
                    if pkg:
                        packages.append(pkg)

            # Look for extras_require
            extras_match = re.search(r"extras_require\s*=\s*\{(.*?)\}", content, re.DOTALL)
            if extras_match:
                # Basic parsing of extras
                for dep in re.findall(r'["\']([^"\']+)["\']', extras_match.group(1)):
                    if re.match(r"^[a-zA-Z]", dep):
                        pkg = self._parse_requirement_string(dep, is_dev=True)
                        if pkg:
                            packages.append(pkg)

        except OSError as e:
            logger.warning("Failed to read setup.py at %s: %s", path, e)
        except Exception as e:
            logger.debug("Unexpected error parsing setup.py at %s: %s", path, e)

        return packages

    def parse_lockfile(self, path: Path) -> list[Package]:
        """Parse lockfile for resolved versions."""
        if path.name == "uv.lock":
            return self._parse_uv_lock(path)
        elif path.name == "poetry.lock":
            return self._parse_poetry_lock(path)
        return []

    def _parse_uv_lock(self, path: Path) -> list[Package]:
        """Parse uv.lock file."""
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
            logger.warning("Failed to parse uv.lock at %s: %s", path, e)
        except OSError as e:
            logger.warning("Failed to read uv.lock at %s: %s", path, e)
        except Exception as e:
            logger.debug("Unexpected error parsing uv.lock at %s: %s", path, e)

        return packages

    def _parse_poetry_lock(self, path: Path) -> list[Package]:
        """Parse poetry.lock file."""
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
            logger.warning("Failed to parse poetry.lock at %s: %s", path, e)
        except OSError as e:
            logger.warning("Failed to read poetry.lock at %s: %s", path, e)
        except Exception as e:
            logger.debug("Unexpected error parsing poetry.lock at %s: %s", path, e)

        return packages

    async def fetch_latest_version(self, client: httpx.AsyncClient, package: Package) -> str | None:
        """Query PyPI for the latest version."""
        try:
            url = f"https://pypi.org/pypi/{package.name}/json"
            response = await client.get(url)

            if response.status_code == 200:
                data = response.json()
                return data.get("info", {}).get("version")

        except httpx.HTTPStatusError as e:
            logger.debug("HTTP error fetching PyPI info for %s: %s", package.name, e)
        except httpx.RequestError as e:
            logger.debug("Request error fetching PyPI info for %s: %s", package.name, e)
        except Exception as e:
            logger.debug("Unexpected error fetching PyPI info for %s: %s", package.name, e)

        return None

    async def fetch_package_info(self, client: httpx.AsyncClient, package: Package) -> dict | None:
        """Fetch full package information from PyPI."""
        try:
            url = f"https://pypi.org/pypi/{package.name}/json"
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
        """Fetch license information from PyPI."""
        try:
            info = await self.fetch_package_info(client, package)
            if info:
                license_str = info.get("info", {}).get("license", "")

                # Try classifiers first for more accurate SPDX ID
                classifiers = info.get("info", {}).get("classifiers", [])
                for classifier in classifiers:
                    if classifier.startswith("License :: OSI Approved ::"):
                        license_name = classifier.split("::")[-1].strip()
                        return self._license_from_classifier(license_name)

                # Fallback to license field
                if license_str:
                    return LicenseInfo(name=license_str, spdx_id=self._guess_spdx_id(license_str))

        except Exception as e:
            logger.debug("Error fetching license for %s: %s", package.name, e)

        return None

    def _license_from_classifier(self, license_name: str) -> LicenseInfo:
        """Create LicenseInfo from a PyPI classifier."""
        spdx_map = {
            "MIT License": "MIT",
            "Apache Software License": "Apache-2.0",
            "BSD License": "BSD-3-Clause",
            "ISC License (ISCL)": "ISC",
            "GNU General Public License v3 (GPLv3)": "GPL-3.0-only",
            "GNU General Public License v2 (GPLv2)": "GPL-2.0-only",
            "Mozilla Public License 2.0 (MPL 2.0)": "MPL-2.0",
        }

        spdx_id = spdx_map.get(license_name)
        if spdx_id:
            return LicenseInfo.from_spdx(spdx_id)

        return LicenseInfo(name=license_name, spdx_id=None)

    def _guess_spdx_id(self, license_str: str) -> str | None:
        """Try to guess SPDX ID from license string."""
        license_lower = license_str.lower()

        if "mit" in license_lower:
            return "MIT"
        if "apache" in license_lower and "2" in license_lower:
            return "Apache-2.0"
        if "bsd" in license_lower:
            if "2" in license_lower:
                return "BSD-2-Clause"
            return "BSD-3-Clause"
        if "isc" in license_lower:
            return "ISC"
        if "gpl" in license_lower:
            if "3" in license_lower:
                return "GPL-3.0-only"
            return "GPL-2.0-only"
        if "mpl" in license_lower or "mozilla" in license_lower:
            return "MPL-2.0"

        return None

    def generate_update_command(
        self, packages: list[Package], include_lockfile: bool = True
    ) -> list[str]:
        """Generate pip/uv update commands."""
        if not packages:
            return []

        package_specs = []
        for pkg in packages:
            if pkg.latest_version:
                spec = f"{pkg.name}>={pkg.latest_version}"
            else:
                spec = pkg.name
            package_specs.append(spec)

        commands = []

        # Check if uv is being used
        if Path("uv.lock").exists():
            # Update pyproject.toml and run uv commands
            commands.append(f"uv add {' '.join(package_specs)}")
            if include_lockfile:
                commands.append("uv lock --upgrade")
                commands.append("uv sync")
        elif Path("poetry.lock").exists():
            # Poetry style
            for pkg in packages:
                if pkg.latest_version:
                    commands.append(f"poetry add {pkg.name}@^{pkg.latest_version}")
            if include_lockfile:
                commands.append("poetry lock")
                commands.append("poetry install")
        else:
            # Standard pip
            commands.append(f"pip install --upgrade {' '.join(package_specs)}")

        return commands

    def supports_workspaces(self) -> bool:
        """Python has limited workspace support."""
        return False
