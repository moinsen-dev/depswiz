"""Tests for tools models."""

import pytest

from depswiz.tools.models import Platform, Tool, ToolsCheckResult, ToolStatus, ToolVersion


class TestToolVersion:
    """Tests for ToolVersion class."""

    def test_parse_simple(self) -> None:
        """Test parsing a simple version string."""
        ver = ToolVersion.parse("1.2.3")
        assert ver is not None
        assert ver.major == 1
        assert ver.minor == 2
        assert ver.patch == 3

    def test_parse_with_v_prefix(self) -> None:
        """Test parsing a version with v prefix."""
        ver = ToolVersion.parse("v1.2.3")
        assert ver is not None
        assert ver.major == 1

    def test_parse_two_parts(self) -> None:
        """Test parsing a version with two parts."""
        ver = ToolVersion.parse("1.2")
        assert ver is not None
        assert ver.major == 1
        assert ver.minor == 2
        assert ver.patch == 0

    def test_parse_one_part(self) -> None:
        """Test parsing a version with one part."""
        ver = ToolVersion.parse("1")
        assert ver is not None
        assert ver.major == 1
        assert ver.minor == 0
        assert ver.patch == 0

    def test_parse_invalid(self) -> None:
        """Test parsing an invalid version returns None."""
        assert ToolVersion.parse("invalid") is None
        assert ToolVersion.parse("") is None

    def test_parse_prerelease(self) -> None:
        """Test parsing a version with prerelease."""
        ver = ToolVersion.parse("1.2.3-beta.1")
        assert ver is not None
        assert ver.prerelease == "beta.1"

    def test_parse_build(self) -> None:
        """Test parsing a version with build metadata."""
        ver = ToolVersion.parse("1.2.3+build123")
        assert ver is not None
        assert ver.build == "build123"

    def test_parse_prerelease_and_build(self) -> None:
        """Test parsing a version with both prerelease and build."""
        ver = ToolVersion.parse("1.2.3-rc.1+build456")
        assert ver is not None
        assert ver.prerelease == "rc.1"
        assert ver.build == "build456"

    def test_str_representation(self) -> None:
        """Test string representation."""
        ver = ToolVersion(1, 2, 3)
        assert str(ver) == "1.2.3"

    def test_comparison_equal(self) -> None:
        """Test version equality."""
        ver1 = ToolVersion(1, 2, 3)
        ver2 = ToolVersion(1, 2, 3)
        assert ver1 == ver2

    def test_comparison_less_than(self) -> None:
        """Test version less than."""
        ver1 = ToolVersion(1, 2, 3)
        ver2 = ToolVersion(1, 2, 4)
        assert ver1 < ver2

    def test_comparison_major(self) -> None:
        """Test version comparison on major."""
        ver1 = ToolVersion(1, 0, 0)
        ver2 = ToolVersion(2, 0, 0)
        assert ver1 < ver2

    def test_comparison_minor(self) -> None:
        """Test version comparison on minor."""
        ver1 = ToolVersion(1, 1, 0)
        ver2 = ToolVersion(1, 2, 0)
        assert ver1 < ver2


class TestToolStatus:
    """Tests for ToolStatus enum."""

    def test_up_to_date_value(self) -> None:
        """Test UP_TO_DATE value."""
        assert ToolStatus.UP_TO_DATE.value == "up_to_date"

    def test_update_available_value(self) -> None:
        """Test UPDATE_AVAILABLE value."""
        assert ToolStatus.UPDATE_AVAILABLE.value == "update_available"

    def test_not_installed_value(self) -> None:
        """Test NOT_INSTALLED value."""
        assert ToolStatus.NOT_INSTALLED.value == "not_installed"


class TestPlatform:
    """Tests for Platform enum."""

    def test_macos_value(self) -> None:
        """Test MACOS value."""
        assert Platform.MACOS.value == "macos"

    def test_linux_value(self) -> None:
        """Test LINUX value."""
        assert Platform.LINUX.value == "linux"

    def test_windows_value(self) -> None:
        """Test WINDOWS value."""
        assert Platform.WINDOWS.value == "windows"


class TestTool:
    """Tests for Tool dataclass."""

    def test_create_tool(self) -> None:
        """Test creating a tool."""
        tool = Tool(
            name="node",
            display_name="Node.js",
            current_version=ToolVersion(18, 0, 0),
            latest_version=ToolVersion(20, 0, 0),
            status=ToolStatus.UPDATE_AVAILABLE,
        )
        assert tool.name == "node"
        assert tool.display_name == "Node.js"
        assert tool.status == ToolStatus.UPDATE_AVAILABLE

    def test_tool_with_update_instruction(self) -> None:
        """Test tool with update instruction."""
        tool = Tool(
            name="node",
            display_name="Node.js",
            current_version=ToolVersion(18, 0, 0),
            latest_version=ToolVersion(20, 0, 0),
            status=ToolStatus.UPDATE_AVAILABLE,
            update_instruction="brew upgrade node",
        )
        assert tool.update_instruction == "brew upgrade node"

    def test_tool_not_installed(self) -> None:
        """Test tool that is not installed."""
        tool = Tool(
            name="go",
            display_name="Go",
            current_version=None,
            latest_version=ToolVersion(1, 21, 0),
            status=ToolStatus.NOT_INSTALLED,
        )
        assert tool.current_version is None
        assert tool.status == ToolStatus.NOT_INSTALLED


class TestToolsCheckResult:
    """Tests for ToolsCheckResult dataclass."""

    def test_create_result(self) -> None:
        """Test creating a check result."""
        result = ToolsCheckResult(
            tools=[
                Tool(
                    name="python",
                    display_name="Python",
                    current_version=ToolVersion(3, 11, 0),
                    latest_version=ToolVersion(3, 12, 0),
                    status=ToolStatus.UPDATE_AVAILABLE,
                ),
            ],
            platform=Platform.MACOS,
        )
        assert len(result.tools) == 1
        assert result.platform == Platform.MACOS

    def test_result_with_multiple_tools(self) -> None:
        """Test result with multiple tools."""
        result = ToolsCheckResult(
            tools=[
                Tool(
                    name="python",
                    display_name="Python",
                    current_version=ToolVersion(3, 12, 0),
                    latest_version=ToolVersion(3, 12, 0),
                    status=ToolStatus.UP_TO_DATE,
                ),
                Tool(
                    name="node",
                    display_name="Node.js",
                    current_version=ToolVersion(18, 0, 0),
                    latest_version=ToolVersion(20, 0, 0),
                    status=ToolStatus.UPDATE_AVAILABLE,
                ),
            ],
            platform=Platform.LINUX,
        )
        assert len(result.tools) == 2

    def test_empty_result(self) -> None:
        """Test empty result."""
        result = ToolsCheckResult(tools=[], platform=Platform.WINDOWS)
        assert len(result.tools) == 0
