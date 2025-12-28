"""Docker plugin for depswiz."""

from pathlib import Path

import httpx

from depswiz.core.logging import get_logger
from depswiz.core.models import LicenseInfo, Package
from depswiz.plugins.base import LanguagePlugin
from depswiz.plugins.docker.compose import parse_compose_file
from depswiz.plugins.docker.dockerfile import DockerImage, parse_dockerfile
from depswiz.plugins.docker.registry import (
    compare_tags,
    get_latest_matching_tag,
)

logger = get_logger("plugins.docker")


class DockerPlugin(LanguagePlugin):
    """Plugin for Docker/container ecosystem.

    Analyzes Dockerfiles and Docker Compose files to check for:
    - Outdated base images
    - Unpinned 'latest' tags
    - Available updates for image tags
    """

    @property
    def name(self) -> str:
        return "docker"

    @property
    def display_name(self) -> str:
        return "Docker"

    @property
    def manifest_patterns(self) -> list[str]:
        return [
            "Dockerfile",
            "Dockerfile.*",
            "*.Dockerfile",
            "docker-compose.yml",
            "docker-compose.yaml",
            "compose.yml",
            "compose.yaml",
        ]

    @property
    def lockfile_patterns(self) -> list[str]:
        # Docker doesn't have lockfiles in the traditional sense
        return []

    @property
    def ecosystem(self) -> str:
        # For future OSV integration with container ecosystems
        return "Docker"

    def detect(self, path: Path) -> bool:
        """Check if this plugin applies to the given path."""
        for pattern in self.manifest_patterns:
            if list(path.glob(pattern)):
                return True
        return False

    def parse_manifest(self, path: Path) -> list[Package]:
        """Parse Dockerfile or compose file and extract image dependencies.

        Each Docker image is represented as a Package where:
        - name: full image reference (e.g., "python", "nginx")
        - current_version: the tag (e.g., "3.13-slim", "latest")
        - constraint: None (Docker doesn't use version constraints)
        - extras: contains additional metadata like digest, stage name
        """
        packages: list[Package] = []

        # Determine file type and parse accordingly
        if path.name.startswith("Dockerfile") or path.name.endswith(".Dockerfile"):
            images = parse_dockerfile(path)
        elif path.name in (
            "docker-compose.yml",
            "docker-compose.yaml",
            "compose.yml",
            "compose.yaml",
        ):
            images = parse_compose_file(path)
        else:
            return packages

        # Convert DockerImage to Package
        for image in images:
            pkg = self._image_to_package(image, path)
            packages.append(pkg)

        return packages

    def _image_to_package(self, image: DockerImage, source_file: Path) -> Package:
        """Convert a DockerImage to a Package."""
        # Store additional metadata in extras
        extras = []
        if image.digest:
            extras.append(f"digest={image.digest}")
        if image.stage_name:
            extras.append(f"stage={image.stage_name}")
        if image.is_latest:
            extras.append("unpinned")

        return Package(
            name=image.name,
            current_version=image.tag,
            constraint=None,
            source_file=source_file,
            extras=extras if extras else None,
            language="docker",
            is_dev=False,
        )

    def parse_lockfile(self, path: Path) -> list[Package]:
        """Docker doesn't have lockfiles, return empty list."""
        return []

    async def fetch_latest_version(
        self, client: httpx.AsyncClient, package: Package
    ) -> str | None:
        """Query Docker Hub for the latest matching tag.

        For example:
        - python:3.11-slim -> finds python:3.13-slim
        - node:18-alpine -> finds node:22-alpine
        """
        # Reconstruct DockerImage from Package
        image = DockerImage(
            name=package.name,
            tag=package.current_version,
        )

        return await get_latest_matching_tag(client, image)

    async def fetch_package_info(
        self, client: httpx.AsyncClient, package: Package
    ) -> dict | None:
        """Fetch image information from Docker Hub.

        Returns basic info structure for compatibility with the interface.
        """
        from depswiz.plugins.docker.registry import fetch_image_tags

        image = DockerImage(name=package.name, tag=package.current_version)
        tags = await fetch_image_tags(client, image)

        if tags:
            return {
                "name": package.name,
                "tags": tags,
                "current_tag": package.current_version,
            }

        return None

    async def fetch_license(
        self, client: httpx.AsyncClient, package: Package
    ) -> LicenseInfo | None:
        """Docker images don't have license info in the registry API.

        License information would require inspecting the actual image layers,
        which is beyond the scope of this plugin.
        """
        return None

    def generate_update_command(
        self, packages: list[Package], include_lockfile: bool = True
    ) -> list[str]:
        """Generate commands to update Docker images.

        Since Docker images are specified in files, we provide guidance
        rather than executable commands.
        """
        if not packages:
            return []

        commands = []

        for pkg in packages:
            if pkg.latest_version and pkg.current_version != pkg.latest_version:
                # Determine if this is a Dockerfile or compose file update
                if pkg.source_file:
                    file_name = pkg.source_file.name
                    if file_name.startswith("Dockerfile") or file_name.endswith(".Dockerfile"):
                        # Dockerfile update instruction
                        old_ref = f"{pkg.name}:{pkg.current_version}" if pkg.current_version else pkg.name
                        new_ref = f"{pkg.name}:{pkg.latest_version}"
                        commands.append(
                            f"# In {file_name}: Update FROM {old_ref} to FROM {new_ref}"
                        )
                    else:
                        # Compose file update instruction
                        old_ref = f"{pkg.name}:{pkg.current_version}" if pkg.current_version else pkg.name
                        new_ref = f"{pkg.name}:{pkg.latest_version}"
                        commands.append(
                            f"# In {file_name}: Update image: {old_ref} to image: {new_ref}"
                        )

        # Add pull command to actually update local images
        if commands:
            commands.append("")
            commands.append("# To pull updated images:")
            for pkg in packages:
                if pkg.latest_version:
                    commands.append(f"docker pull {pkg.name}:{pkg.latest_version}")

        return commands

    def find_manifest_files(self, path: Path, recursive: bool = False) -> list[Path]:
        """Find all Docker-related files in the given path.

        Overridden to handle Dockerfile patterns more carefully.
        """
        found: list[Path] = []

        for pattern in self.manifest_patterns:
            if recursive:
                found.extend(path.rglob(pattern))
            else:
                found.extend(path.glob(pattern))

        # Remove duplicates and sort
        return sorted(set(found))

    def is_package_outdated(self, package: Package) -> bool:
        """Check if a Docker image package is outdated.

        Special handling for Docker:
        - Images with 'latest' tag are always considered needing attention
        - Compares current and latest tags using semantic versioning
        """
        # Check for unpinned 'latest' tag
        if package.extras and "unpinned" in package.extras:
            return True

        return compare_tags(package.current_version, package.latest_version)
