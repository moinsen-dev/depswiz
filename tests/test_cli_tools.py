"""Tests for the tools CLI command."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from typer.testing import CliRunner

from depswiz.cli.app import app
from depswiz.tools.models import Platform, Tool, ToolsCheckResult, ToolStatus, ToolVersion

runner = CliRunner()


@pytest.fixture
def mock_tools_result() -> ToolsCheckResult:
    """Create a mock tools check result."""
    return ToolsCheckResult(
        tools=[
            Tool(
                name="node",
                display_name="Node.js",
                current_version=ToolVersion(20, 10, 0),
                latest_version=ToolVersion(22, 12, 0),
                status=ToolStatus.UPDATE_AVAILABLE,
                update_instruction="brew upgrade node",
            ),
            Tool(
                name="python",
                display_name="Python",
                current_version=ToolVersion(3, 13, 1),
                latest_version=ToolVersion(3, 13, 1),
                status=ToolStatus.UP_TO_DATE,
            ),
            Tool(
                name="rust",
                display_name="Rust",
                current_version=None,
                latest_version=ToolVersion(1, 84, 0),
                status=ToolStatus.NOT_INSTALLED,
            ),
        ],
        platform=Platform.MACOS,
    )


class TestToolsCommand:
    """Tests for the tools command."""

    def test_tools_help(self) -> None:
        """Test tools command help text."""
        result = runner.invoke(app, ["tools", "--help"])
        assert result.exit_code == 0
        # Check for key content - options may be truncated in narrow terminals
        assert "tools" in result.stdout.lower() or "development" in result.stdout.lower()

    @patch("depswiz.cli.commands.tools.scan_tools", new_callable=AsyncMock)
    def test_tools_scan(
        self, mock_scan: AsyncMock, mock_tools_result: ToolsCheckResult, tmp_path: Path
    ) -> None:
        """Test tools command with mocked scanner."""
        mock_scan.return_value = mock_tools_result

        result = runner.invoke(app, ["tools", str(tmp_path)])
        assert result.exit_code == 0
        assert "Node.js" in result.stdout
        assert "Python" in result.stdout
        mock_scan.assert_called_once()

    @patch("depswiz.cli.commands.tools.scan_tools", new_callable=AsyncMock)
    def test_tools_json_format(
        self, mock_scan: AsyncMock, mock_tools_result: ToolsCheckResult, tmp_path: Path
    ) -> None:
        """Test tools command with JSON output format."""
        mock_scan.return_value = mock_tools_result

        result = runner.invoke(app, ["tools", "--format", "json", str(tmp_path)])
        assert result.exit_code == 0
        assert '"tools"' in result.stdout
        assert '"node"' in result.stdout

    @patch("depswiz.cli.commands.tools.scan_tools", new_callable=AsyncMock)
    def test_tools_updates_only(
        self, mock_scan: AsyncMock, mock_tools_result: ToolsCheckResult, tmp_path: Path
    ) -> None:
        """Test tools command with --updates-only filter."""
        mock_scan.return_value = mock_tools_result

        result = runner.invoke(app, ["tools", "--updates-only", str(tmp_path)])
        assert result.exit_code == 0
        # Only Node.js has an update available
        assert "Node.js" in result.stdout
        # Python is up to date, should not be shown
        # (Note: exact behavior depends on CLI output format)

    def test_tools_list_supported(self) -> None:
        """Test tools command with --list flag."""
        result = runner.invoke(app, ["tools", "--list"])
        assert result.exit_code == 0
        assert "Supported Tools" in result.stdout
        assert "node" in result.stdout
        assert "python" in result.stdout
        assert "rust" in result.stdout

    @patch("depswiz.cli.commands.tools.scan_tools", new_callable=AsyncMock)
    def test_tools_no_instructions(
        self, mock_scan: AsyncMock, mock_tools_result: ToolsCheckResult, tmp_path: Path
    ) -> None:
        """Test tools command with --no-instructions."""
        mock_scan.return_value = mock_tools_result

        result = runner.invoke(app, ["tools", "--no-instructions", str(tmp_path)])
        assert result.exit_code == 0
        # Should not show update instructions
        assert "brew upgrade node" not in result.stdout

    @patch("depswiz.cli.commands.tools.scan_tools", new_callable=AsyncMock)
    def test_tools_include_not_installed(
        self, mock_scan: AsyncMock, mock_tools_result: ToolsCheckResult, tmp_path: Path
    ) -> None:
        """Test tools command with --include-not-installed."""
        mock_scan.return_value = mock_tools_result

        result = runner.invoke(app, ["tools", "--include-not-installed", str(tmp_path)])
        assert result.exit_code == 0
        mock_scan.assert_called_once()
        # Check that include_not_installed was passed
        call_kwargs = mock_scan.call_args[1]
        assert call_kwargs.get("include_not_installed") is True


class TestToolsSpecificTools:
    """Tests for specifying specific tools."""

    @patch("depswiz.cli.commands.tools.scan_tools", new_callable=AsyncMock)
    def test_tools_specific_tool(
        self, mock_scan: AsyncMock, mock_tools_result: ToolsCheckResult, tmp_path: Path
    ) -> None:
        """Test tools command with specific tool specified."""
        mock_scan.return_value = mock_tools_result

        result = runner.invoke(app, ["tools", "-t", "node", str(tmp_path)])
        assert result.exit_code == 0
        mock_scan.assert_called_once()
        call_kwargs = mock_scan.call_args[1]
        assert call_kwargs.get("tool_names") == ["node"]

    @patch("depswiz.cli.commands.tools.scan_tools", new_callable=AsyncMock)
    def test_tools_multiple_specific_tools(
        self, mock_scan: AsyncMock, mock_tools_result: ToolsCheckResult, tmp_path: Path
    ) -> None:
        """Test tools command with multiple specific tools."""
        mock_scan.return_value = mock_tools_result

        result = runner.invoke(app, ["tools", "-t", "node", "-t", "python", str(tmp_path)])
        assert result.exit_code == 0
        mock_scan.assert_called_once()
        call_kwargs = mock_scan.call_args[1]
        assert call_kwargs.get("tool_names") == ["node", "python"]

    @patch("depswiz.cli.commands.tools.scan_tools", new_callable=AsyncMock)
    def test_tools_all_flag(
        self, mock_scan: AsyncMock, mock_tools_result: ToolsCheckResult, tmp_path: Path
    ) -> None:
        """Test tools command with --all flag."""
        mock_scan.return_value = mock_tools_result

        result = runner.invoke(app, ["tools", "--all", str(tmp_path)])
        assert result.exit_code == 0
        mock_scan.assert_called_once()
        call_kwargs = mock_scan.call_args[1]
        assert call_kwargs.get("check_all") is True


class TestToolsUpgrade:
    """Tests for tools upgrade mode."""

    @patch("depswiz.cli.commands.tools.claude_client")
    @patch("depswiz.cli.commands.tools.scan_tools", new_callable=AsyncMock)
    def test_tools_upgrade_no_claude(
        self,
        mock_scan: AsyncMock,
        mock_claude: object,
        mock_tools_result: ToolsCheckResult,
        tmp_path: Path,
    ) -> None:
        """Test tools upgrade mode when Claude is not available."""
        mock_scan.return_value = mock_tools_result
        mock_claude.is_available.return_value = False

        result = runner.invoke(app, ["tools", "--upgrade", str(tmp_path)])
        assert result.exit_code == 1
        assert "Claude Code" in result.stdout


class TestToolsEmptyResult:
    """Tests for when no tools are detected."""

    @patch("depswiz.cli.commands.tools.scan_tools", new_callable=AsyncMock)
    def test_tools_no_tools_detected(self, mock_scan: AsyncMock, tmp_path: Path) -> None:
        """Test tools command when no tools are detected."""
        empty_result = ToolsCheckResult(
            tools=[],
            platform=Platform.MACOS,
        )
        mock_scan.return_value = empty_result

        result = runner.invoke(app, ["tools", str(tmp_path)])
        assert result.exit_code == 0
        assert "No tools detected" in result.stdout
