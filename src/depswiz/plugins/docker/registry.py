"""Docker Hub registry API client."""

import re

import httpx

from depswiz.core.logging import get_logger
from depswiz.plugins.docker.dockerfile import DockerImage

logger = get_logger("plugins.docker.registry")

# Docker Hub API base URL
DOCKER_HUB_API = "https://hub.docker.com/v2"


async def fetch_image_tags(
    client: httpx.AsyncClient,
    image: DockerImage,
    page_size: int = 100,
) -> list[str]:
    """Fetch available tags for a Docker image from Docker Hub.

    Args:
        client: Async HTTP client
        image: Docker image to look up
        page_size: Number of tags to fetch per request

    Returns:
        List of available tag names
    """
    # Only support Docker Hub for now
    if image.registry != "docker.io":
        logger.debug("Skipping non-Docker Hub registry: %s", image.registry)
        return []

    namespace = image.namespace
    repository = image.repository

    try:
        url = f"{DOCKER_HUB_API}/namespaces/{namespace}/repositories/{repository}/tags"
        response = await client.get(
            url,
            params={"page_size": page_size},
            timeout=10.0,
        )

        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            return [tag["name"] for tag in results if "name" in tag]

        if response.status_code == 404:
            logger.debug("Image not found on Docker Hub: %s/%s", namespace, repository)
        else:
            logger.debug(
                "Docker Hub API returned %s for %s/%s",
                response.status_code,
                namespace,
                repository,
            )

    except httpx.RequestError as e:
        logger.debug("Request error fetching Docker Hub tags for %s: %s", image.name, e)
    except Exception as e:
        logger.debug("Unexpected error fetching Docker Hub tags for %s: %s", image.name, e)

    return []


async def get_latest_semver_tag(
    client: httpx.AsyncClient,
    image: DockerImage,
) -> str | None:
    """Get the latest semantic version tag for an image.

    This finds tags that look like semantic versions (e.g., 3.13, 3.13.1)
    and returns the highest one.

    Args:
        client: Async HTTP client
        image: Docker image to look up

    Returns:
        Latest semver tag, or None if no semver tags found
    """
    tags = await fetch_image_tags(client, image)
    if not tags:
        return None

    # Filter to semver-like tags
    semver_pattern = re.compile(r"^v?(\d+)(?:\.(\d+))?(?:\.(\d+))?$")
    semver_tags: list[tuple[tuple[int, int, int], str]] = []

    for tag in tags:
        match = semver_pattern.match(tag)
        if match:
            major = int(match.group(1))
            minor = int(match.group(2)) if match.group(2) else 0
            patch = int(match.group(3)) if match.group(3) else 0
            semver_tags.append(((major, minor, patch), tag))

    if not semver_tags:
        return None

    # Sort by version tuple and return highest
    semver_tags.sort(key=lambda x: x[0], reverse=True)
    return semver_tags[0][1]


async def get_latest_matching_tag(
    client: httpx.AsyncClient,
    image: DockerImage,
) -> str | None:
    """Get the latest tag matching the current tag's suffix pattern.

    For example:
    - python:3.11-slim -> finds python:3.13-slim
    - node:18-alpine -> finds node:22-alpine
    - redis:6 -> finds redis:7

    Args:
        client: Async HTTP client
        image: Docker image to look up

    Returns:
        Latest matching tag, or None if none found
    """
    if not image.tag or image.tag == "latest":
        return await get_latest_semver_tag(client, image)

    tags = await fetch_image_tags(client, image)
    if not tags:
        return None

    # Extract suffix from current tag (e.g., "-slim", "-alpine")
    # Pattern: version[-suffix]
    current_match = re.match(r"^v?(\d+(?:\.\d+)*)(.*)$", image.tag)
    if not current_match:
        # Non-semver tag, can't compare
        return None

    suffix = current_match.group(2)  # e.g., "-slim", "-alpine", ""

    # Find all tags with the same suffix
    version_pattern = re.compile(rf"^v?(\d+)(?:\.(\d+))?(?:\.(\d+))?{re.escape(suffix)}$")
    matching_tags: list[tuple[tuple[int, int, int], str]] = []

    for tag in tags:
        match = version_pattern.match(tag)
        if match:
            major = int(match.group(1))
            minor = int(match.group(2)) if match.group(2) else 0
            patch = int(match.group(3)) if match.group(3) else 0
            matching_tags.append(((major, minor, patch), tag))

    if not matching_tags:
        return None

    # Sort by version tuple and return highest
    matching_tags.sort(key=lambda x: x[0], reverse=True)
    return matching_tags[0][1]


def compare_tags(current: str | None, latest: str | None) -> bool:
    """Compare two tags to determine if an update is available.

    Args:
        current: Current tag (e.g., "3.11-slim")
        latest: Latest tag (e.g., "3.13-slim")

    Returns:
        True if latest is newer than current
    """
    if not current or not latest:
        return False

    if current == latest:
        return False

    # Extract version numbers for comparison
    current_match = re.match(r"^v?(\d+)(?:\.(\d+))?(?:\.(\d+))?", current)
    latest_match = re.match(r"^v?(\d+)(?:\.(\d+))?(?:\.(\d+))?", latest)

    if not current_match or not latest_match:
        # Can't compare non-semver tags
        return False

    def version_tuple(match: re.Match) -> tuple[int, int, int]:
        return (
            int(match.group(1)),
            int(match.group(2)) if match.group(2) else 0,
            int(match.group(3)) if match.group(3) else 0,
        )

    return version_tuple(latest_match) > version_tuple(current_match)
