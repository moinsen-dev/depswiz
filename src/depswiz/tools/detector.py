"""Tool detection via subprocess calls."""

import platform
import re
import subprocess
from pathlib import Path

from depswiz.tools.definitions import get_tool_definition, get_tools_for_project_files
from depswiz.tools.models import Platform, Tool, ToolStatus, ToolVersion


def get_platform() -> Platform:
    """Detect the current operating system platform."""
    system = platform.system().lower()
    if system == "darwin":
        return Platform.MACOS
    elif system == "linux":
        return Platform.LINUX
    elif system == "windows":
        return Platform.WINDOWS
    return Platform.UNKNOWN


def detect_tool(tool_name: str, current_platform: Platform | None = None) -> Tool:
    """Detect if a tool is installed and get its version.

    Args:
        tool_name: Name of the tool to detect
        current_platform: Platform for update instructions (auto-detected if None)

    Returns:
        Tool object with version info and status
    """
    definition = get_tool_definition(tool_name)
    if not definition:
        return Tool(
            name=tool_name,
            display_name=tool_name,
            status=ToolStatus.ERROR,
            error_message=f"Unknown tool: {tool_name}",
        )

    if current_platform is None:
        current_platform = get_platform()

    # Get update instruction for current platform
    platform_key = current_platform.value if current_platform != Platform.UNKNOWN else "linux"
    update_instruction = definition.update_instructions.get(platform_key, "")

    try:
        result = subprocess.run(
            definition.version_command,
            capture_output=True,
            text=True,
            timeout=10,
        )

        # Some tools output version to stderr (like dart)
        output = result.stdout or result.stderr

        # Parse version from output
        match = re.search(definition.version_regex, output)
        if match:
            version_str = match.group(1)
            current_version = ToolVersion.parse(version_str)

            return Tool(
                name=definition.name,
                display_name=definition.display_name,
                current_version=current_version,
                status=ToolStatus.UP_TO_DATE,  # Will be updated after comparing with latest
                update_instruction=update_instruction,
            )
        else:
            # Command succeeded but couldn't parse version
            return Tool(
                name=definition.name,
                display_name=definition.display_name,
                status=ToolStatus.ERROR,
                error_message=f"Could not parse version from: {output[:100]}",
                update_instruction=update_instruction,
            )

    except FileNotFoundError:
        return Tool(
            name=definition.name,
            display_name=definition.display_name,
            status=ToolStatus.NOT_INSTALLED,
            update_instruction=update_instruction,
        )
    except subprocess.TimeoutExpired:
        return Tool(
            name=definition.name,
            display_name=definition.display_name,
            status=ToolStatus.ERROR,
            error_message="Command timed out",
            update_instruction=update_instruction,
        )
    except Exception as e:
        return Tool(
            name=definition.name,
            display_name=definition.display_name,
            status=ToolStatus.ERROR,
            error_message=str(e),
            update_instruction=update_instruction,
        )


def detect_project_tools(path: Path) -> list[str]:
    """Auto-detect relevant tools based on project files.

    Args:
        path: Path to project root directory

    Returns:
        List of tool names relevant to this project
    """
    if not path.is_dir():
        return []

    # Get list of files in project root
    try:
        files = [f.name for f in path.iterdir() if f.is_file()]
    except PermissionError:
        return []

    return get_tools_for_project_files(files)


def detect_all_tools(tool_names: list[str], current_platform: Platform | None = None) -> list[Tool]:
    """Detect multiple tools at once.

    Args:
        tool_names: List of tool names to detect
        current_platform: Platform for update instructions

    Returns:
        List of Tool objects
    """
    if current_platform is None:
        current_platform = get_platform()

    return [detect_tool(name, current_platform) for name in tool_names]
