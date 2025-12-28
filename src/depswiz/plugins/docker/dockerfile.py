"""Dockerfile parsing utilities."""

import re
from dataclasses import dataclass
from pathlib import Path

from depswiz.core.logging import get_logger

logger = get_logger("plugins.docker.dockerfile")


@dataclass
class DockerImage:
    """Represents a Docker image reference."""

    name: str  # e.g., "python", "library/python", "gcr.io/project/image"
    tag: str | None = None  # e.g., "3.13-slim", "latest"
    digest: str | None = None  # e.g., "sha256:abc123..."
    stage_name: str | None = None  # For multi-stage builds, e.g., "builder"
    line_number: int | None = None  # Line in Dockerfile

    @property
    def registry(self) -> str:
        """Extract registry from image name."""
        # If name contains a dot or colon before first slash, it's a registry
        if "/" in self.name:
            first_part = self.name.split("/")[0]
            if "." in first_part or ":" in first_part:
                return first_part
        return "docker.io"

    @property
    def is_official(self) -> bool:
        """Check if this is an official Docker Hub image."""
        return self.registry == "docker.io" and "/" not in self.name

    @property
    def namespace(self) -> str:
        """Get namespace (user/org) for the image."""
        if self.is_official:
            return "library"
        if "/" in self.name:
            parts = self.name.split("/")
            if self.registry != "docker.io":
                # Skip registry part
                return parts[1] if len(parts) > 2 else parts[-1].split("/")[0]
            return parts[0]
        return "library"

    @property
    def repository(self) -> str:
        """Get repository name without namespace/registry."""
        if "/" in self.name:
            return self.name.split("/")[-1]
        return self.name

    @property
    def is_latest(self) -> bool:
        """Check if using 'latest' tag (unpinned)."""
        return self.tag is None or self.tag == "latest"

    @property
    def full_reference(self) -> str:
        """Get the full image reference as it would appear in FROM."""
        ref = self.name
        if self.tag:
            ref = f"{ref}:{self.tag}"
        if self.digest:
            ref = f"{ref}@{self.digest}"
        return ref

    def __str__(self) -> str:
        return self.full_reference


def parse_dockerfile(path: Path) -> list[DockerImage]:
    """Parse a Dockerfile and extract all base images.

    Handles:
    - Simple FROM statements
    - Multi-stage builds (FROM ... AS name)
    - Digest pinning (FROM image@sha256:...)
    - ARG substitution in FROM (limited support)

    Args:
        path: Path to the Dockerfile

    Returns:
        List of DockerImage objects representing base images
    """
    images: list[DockerImage] = []

    try:
        content = path.read_text()
        lines = content.splitlines()

        # Track ARG values defined before FROM (for dynamic base images)
        build_args: dict[str, str] = {}

        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()

            # Skip comments and empty lines
            if not stripped or stripped.startswith("#"):
                continue

            # Track ARG definitions (only those before first FROM matter for base image)
            if stripped.upper().startswith("ARG "):
                arg_match = re.match(r"ARG\s+(\w+)(?:=(.*))?", stripped, re.IGNORECASE)
                if arg_match:
                    arg_name = arg_match.group(1)
                    arg_value = arg_match.group(2) or ""
                    build_args[arg_name] = arg_value.strip().strip('"').strip("'")

            # Parse FROM statements
            if stripped.upper().startswith("FROM "):
                image = _parse_from_statement(stripped, line_num, build_args)
                if image:
                    images.append(image)

    except OSError as e:
        logger.warning("Failed to read Dockerfile at %s: %s", path, e)
    except Exception as e:
        logger.debug("Unexpected error parsing Dockerfile at %s: %s", path, e)

    return images


def _parse_from_statement(
    line: str, line_number: int, build_args: dict[str, str]
) -> DockerImage | None:
    """Parse a FROM statement and extract image details.

    Examples:
        FROM python:3.13
        FROM python:3.13-slim AS builder
        FROM python@sha256:abc123...
        FROM ${BASE_IMAGE}:${VERSION}
        FROM --platform=linux/amd64 python:3.13
    """
    # Remove FROM keyword and handle --platform flag
    from_pattern = r"FROM\s+(?:--platform=\S+\s+)?(\S+)(?:\s+AS\s+(\w+))?"
    match = re.match(from_pattern, line, re.IGNORECASE)

    if not match:
        return None

    image_ref = match.group(1)
    stage_name = match.group(2)

    # Substitute build args (e.g., ${BASE_IMAGE})
    for arg_name, arg_value in build_args.items():
        image_ref = image_ref.replace(f"${{{arg_name}}}", arg_value)
        image_ref = image_ref.replace(f"${arg_name}", arg_value)

    # Skip if we still have unresolved variables
    if "$" in image_ref:
        logger.debug("Skipping FROM with unresolved variable: %s", image_ref)
        return None

    # Skip scratch images
    if image_ref.lower() == "scratch":
        return None

    # Parse image reference
    name, tag, digest = _parse_image_reference(image_ref)

    return DockerImage(
        name=name,
        tag=tag,
        digest=digest,
        stage_name=stage_name,
        line_number=line_number,
    )


def _parse_image_reference(ref: str) -> tuple[str, str | None, str | None]:
    """Parse an image reference into name, tag, and digest.

    Examples:
        python -> (python, None, None)
        python:3.13 -> (python, 3.13, None)
        python@sha256:abc -> (python, None, sha256:abc)
        python:3.13@sha256:abc -> (python, 3.13, sha256:abc)
        gcr.io/project/image:tag -> (gcr.io/project/image, tag, None)
    """
    name = ref
    tag = None
    digest = None

    # Extract digest first (after @)
    if "@" in name:
        name, digest = name.rsplit("@", 1)

    # Extract tag (after : but not if it's a port in registry)
    # Registry ports look like: localhost:5000/image
    # Tags look like: image:tag
    if ":" in name:
        # Find the last : that's not part of a registry address
        last_colon = name.rfind(":")
        # Check if there's a / after this colon (would mean it's a registry port)
        if "/" not in name[last_colon:]:
            name, tag = name.rsplit(":", 1)

    return name, tag, digest
