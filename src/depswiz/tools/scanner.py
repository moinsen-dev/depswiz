"""Main scanning orchestration for development tools."""

from pathlib import Path

import httpx

from depswiz.tools.definitions import get_all_tool_names
from depswiz.tools.detector import detect_all_tools, detect_project_tools, get_platform
from depswiz.tools.models import ToolsCheckResult, ToolStatus
from depswiz.tools.version_sources import fetch_all_latest_versions


async def scan_tools(
    path: Path | None = None,
    tool_names: list[str] | None = None,
    check_all: bool = False,
    include_not_installed: bool = False,
) -> ToolsCheckResult:
    """Scan development tools and check for updates.

    Args:
        path: Project path for auto-detection (default: current directory)
        tool_names: Specific tools to check (overrides auto-detection)
        check_all: Check all supported tools
        include_not_installed: Include tools that are not installed

    Returns:
        ToolsCheckResult with all tool information
    """
    current_platform = get_platform()

    # Determine which tools to check
    if tool_names:
        tools_to_check = tool_names
    elif check_all:
        tools_to_check = get_all_tool_names()
    else:
        # Auto-detect based on project files
        project_path = path or Path.cwd()
        tools_to_check = detect_project_tools(project_path)

        # If no project-specific tools found, check common ones
        if not tools_to_check:
            tools_to_check = ["python", "node", "uv", "rust", "docker"]

    # Detect installed tools
    tools = detect_all_tools(tools_to_check, current_platform)

    # Filter out not installed if requested
    if not include_not_installed:
        installed_tools = [t for t in tools if t.status != ToolStatus.NOT_INSTALLED]
        installed_names = [t.name for t in installed_tools]
    else:
        installed_tools = tools
        installed_names = [t.name for t in tools if t.status != ToolStatus.NOT_INSTALLED]

    # Fetch latest versions for installed tools
    if installed_names:
        async with httpx.AsyncClient() as client:
            latest_versions = await fetch_all_latest_versions(client, installed_names)

            # Update tools with latest version info and status
            for tool in installed_tools:
                if tool.name in latest_versions:
                    latest = latest_versions[tool.name]
                    tool.latest_version = latest

                    # Update status based on version comparison
                    if tool.current_version and latest:
                        if tool.current_version < latest:
                            tool.status = ToolStatus.UPDATE_AVAILABLE
                        else:
                            tool.status = ToolStatus.UP_TO_DATE

    return ToolsCheckResult(
        tools=installed_tools,
        platform=current_platform,
    )


def format_tools_summary(result: ToolsCheckResult) -> str:
    """Format a brief summary of tool check results.

    Args:
        result: The tools check result

    Returns:
        Summary string
    """
    lines = []

    if result.updates_available > 0:
        lines.append(f"{result.updates_available} tool(s) have updates available")

    if result.up_to_date > 0:
        lines.append(f"{result.up_to_date} tool(s) are up to date")

    if result.not_installed > 0:
        lines.append(f"{result.not_installed} tool(s) not installed")

    return "\n".join(lines)
