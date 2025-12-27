"""Fetch latest versions from official sources and GitHub releases."""

import httpx

from depswiz.core.logging import get_logger
from depswiz.tools.definitions import get_tool_definition
from depswiz.tools.models import ToolVersion

logger = get_logger("tools.version_sources")


class VersionFetchError(Exception):
    """Error fetching latest version."""

    pass


def extract_version_from_tag(tag_name: str, tool_name: str) -> str | None:
    """Extract version string from various tag formats.

    Different tools use different tag formats:
    - Standard: v1.2.3 or 1.2.3
    - Yarn Berry: @yarnpkg/cli/4.12.0
    - Bun: bun-v1.3.5
    - Flutter: 3.19.0

    Args:
        tag_name: The raw tag name from GitHub
        tool_name: Name of the tool for format-specific handling

    Returns:
        Cleaned version string or None
    """
    if not tag_name:
        return None

    # Handle Yarn Berry format: @yarnpkg/cli/4.12.0
    if "/" in tag_name and tool_name == "yarn":
        parts = tag_name.split("/")
        return parts[-1] if parts else None

    # Handle Bun format: bun-v1.3.5
    if tag_name.startswith("bun-"):
        return tag_name.replace("bun-", "")

    # Handle standard formats (v1.2.3, 1.2.3, etc.)
    return tag_name


async def fetch_latest_from_github(
    client: httpx.AsyncClient,
    repo: str,
    tool_name: str = "",
) -> ToolVersion | None:
    """Fetch latest version from GitHub releases.

    Args:
        client: Async HTTP client
        repo: GitHub repo in format "owner/repo"
        tool_name: Name of the tool for format-specific handling

    Returns:
        Latest version or None if not found
    """
    url = f"https://api.github.com/repos/{repo}/releases/latest"

    try:
        response = await client.get(
            url,
            headers={"Accept": "application/vnd.github.v3+json"},
            timeout=10.0,
        )

        if response.status_code == 404:
            # Try tags instead (some repos don't use releases)
            return await fetch_latest_from_github_tags(client, repo, tool_name)

        if response.status_code != 200:
            return None

        data = response.json()
        tag_name = data.get("tag_name", "")

        # Extract version with tool-specific handling
        version_str = extract_version_from_tag(tag_name, tool_name)
        return ToolVersion.parse(version_str) if version_str else None

    except httpx.HTTPStatusError as e:
        logger.debug("HTTP error fetching GitHub releases for %s: %s", repo, e)
    except httpx.RequestError as e:
        logger.debug("Request error fetching GitHub releases for %s: %s", repo, e)
    except Exception as e:
        logger.debug("Unexpected error fetching GitHub releases for %s: %s", repo, e)

    return None


async def fetch_latest_from_github_tags(
    client: httpx.AsyncClient,
    repo: str,
    tool_name: str = "",
) -> ToolVersion | None:
    """Fetch latest version from GitHub tags (fallback).

    Args:
        client: Async HTTP client
        repo: GitHub repo in format "owner/repo"
        tool_name: Name of the tool for format-specific handling

    Returns:
        Latest version or None if not found
    """
    url = f"https://api.github.com/repos/{repo}/tags"

    try:
        response = await client.get(
            url,
            headers={"Accept": "application/vnd.github.v3+json"},
            timeout=10.0,
        )

        if response.status_code != 200:
            return None

        tags = response.json()
        if not tags:
            return None

        # Find first tag that looks like a version
        for tag in tags[:10]:  # Check first 10 tags
            tag_name = tag.get("name", "")
            version_str = extract_version_from_tag(tag_name, tool_name)
            if version_str:
                version = ToolVersion.parse(version_str)
                if version and not version.prerelease:  # Skip prereleases
                    return version

        # If no stable version, return first parseable one
        for tag in tags[:10]:
            version_str = extract_version_from_tag(tag.get("name", ""), tool_name)
            if version_str:
                version = ToolVersion.parse(version_str)
                if version:
                    return version

        return None

    except httpx.HTTPStatusError as e:
        logger.debug("HTTP error fetching GitHub tags for %s: %s", repo, e)
    except httpx.RequestError as e:
        logger.debug("Request error fetching GitHub tags for %s: %s", repo, e)
    except Exception as e:
        logger.debug("Unexpected error fetching GitHub tags for %s: %s", repo, e)

    return None


async def fetch_latest_nodejs(client: httpx.AsyncClient) -> ToolVersion | None:
    """Fetch latest Node.js LTS version from official API.

    Args:
        client: Async HTTP client

    Returns:
        Latest LTS version or None
    """
    url = "https://nodejs.org/dist/index.json"

    try:
        response = await client.get(url, timeout=10.0)

        if response.status_code != 200:
            return None

        releases = response.json()

        # Find latest LTS version
        for release in releases:
            if release.get("lts"):  # LTS releases have a codename
                version_str = release.get("version", "")
                return ToolVersion.parse(version_str)

        # Fallback to latest if no LTS found
        if releases:
            return ToolVersion.parse(releases[0].get("version", ""))

        return None

    except httpx.HTTPStatusError as e:
        logger.debug("HTTP error fetching Node.js version: %s", e)
    except httpx.RequestError as e:
        logger.debug("Request error fetching Node.js version: %s", e)
    except Exception as e:
        logger.debug("Unexpected error fetching Node.js version: %s", e)

    return None


async def fetch_latest_go(client: httpx.AsyncClient) -> ToolVersion | None:
    """Fetch latest Go version from official API.

    Args:
        client: Async HTTP client

    Returns:
        Latest stable version or None
    """
    url = "https://go.dev/dl/?mode=json"

    try:
        response = await client.get(url, timeout=10.0)

        if response.status_code != 200:
            return None

        releases = response.json()

        # First stable release in list
        for release in releases:
            if release.get("stable"):
                version_str = release.get("version", "").replace("go", "")
                return ToolVersion.parse(version_str)

        return None

    except httpx.HTTPStatusError as e:
        logger.debug("HTTP error fetching Go version: %s", e)
    except httpx.RequestError as e:
        logger.debug("Request error fetching Go version: %s", e)
    except Exception as e:
        logger.debug("Unexpected error fetching Go version: %s", e)

    return None


async def fetch_latest_dart(client: httpx.AsyncClient) -> ToolVersion | None:
    """Fetch latest Dart SDK version from official Google Storage API.

    Args:
        client: Async HTTP client

    Returns:
        Latest stable version or None
    """
    url = "https://storage.googleapis.com/dart-archive/channels/stable/release/latest/VERSION"

    try:
        response = await client.get(url, timeout=10.0)

        if response.status_code != 200:
            return None

        data = response.json()
        version_str = data.get("version", "")
        return ToolVersion.parse(version_str)

    except httpx.HTTPStatusError as e:
        logger.debug("HTTP error fetching Dart version: %s", e)
    except httpx.RequestError as e:
        logger.debug("Request error fetching Dart version: %s", e)
    except Exception as e:
        logger.debug("Unexpected error fetching Dart version: %s", e)

    return None


async def fetch_latest_flutter(client: httpx.AsyncClient) -> ToolVersion | None:
    """Fetch latest Flutter version from official releases.

    Args:
        client: Async HTTP client

    Returns:
        Latest stable version or None
    """
    # Flutter publishes releases JSON for each platform
    url = "https://storage.googleapis.com/flutter_infra_release/releases/releases_macos.json"

    try:
        response = await client.get(url, timeout=10.0)

        if response.status_code != 200:
            return None

        data = response.json()
        # Get current stable release hash
        current_stable = data.get("current_release", {}).get("stable")
        if not current_stable:
            return None

        # Find the release with that hash
        releases = data.get("releases", [])
        for release in releases:
            if release.get("hash") == current_stable and release.get("channel") == "stable":
                version_str = release.get("version", "")
                return ToolVersion.parse(version_str)

        return None

    except httpx.HTTPStatusError as e:
        logger.debug("HTTP error fetching Flutter version: %s", e)
    except httpx.RequestError as e:
        logger.debug("Request error fetching Flutter version: %s", e)
    except Exception as e:
        logger.debug("Unexpected error fetching Flutter version: %s", e)

    return None


async def fetch_latest_version(
    client: httpx.AsyncClient,
    tool_name: str,
) -> ToolVersion | None:
    """Fetch latest version for a tool from appropriate source.

    Args:
        client: Async HTTP client
        tool_name: Name of the tool

    Returns:
        Latest version or None if not found
    """
    definition = get_tool_definition(tool_name)
    if not definition:
        return None

    # Use tool-specific official APIs
    if tool_name == "node":
        return await fetch_latest_nodejs(client)
    elif tool_name == "go":
        return await fetch_latest_go(client)
    elif tool_name == "dart":
        return await fetch_latest_dart(client)
    elif tool_name == "flutter":
        return await fetch_latest_flutter(client)

    # Fall back to GitHub releases
    if definition.github_repo:
        return await fetch_latest_from_github(client, definition.github_repo, tool_name)

    return None


async def fetch_all_latest_versions(
    client: httpx.AsyncClient,
    tool_names: list[str],
) -> dict[str, ToolVersion | None]:
    """Fetch latest versions for multiple tools concurrently.

    Args:
        client: Async HTTP client
        tool_names: List of tool names

    Returns:
        Dictionary mapping tool names to their latest versions
    """
    import asyncio

    async def fetch_one(name: str) -> tuple[str, ToolVersion | None]:
        version = await fetch_latest_version(client, name)
        return (name, version)

    results = await asyncio.gather(*[fetch_one(name) for name in tool_names])
    return dict(results)
