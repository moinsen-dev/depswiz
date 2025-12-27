"""Tests for the check CLI command."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from typer.testing import CliRunner

from depswiz.cli.app import app
from depswiz.core.models import CheckResult, Package, UpdateType

runner = CliRunner()


@pytest.fixture
def mock_check_result() -> CheckResult:
    """Create a mock check result for testing."""
    return CheckResult(
        packages=[
            Package(
                name="requests",
                language="python",
                constraint=">=2.28.0",
                current_version="2.28.0",
                latest_version="2.31.0",
                update_type=UpdateType.MINOR,
                is_dev=False,
            ),
            Package(
                name="httpx",
                language="python",
                constraint=">=0.25.0",
                current_version="0.25.0",
                latest_version="0.25.0",
                update_type=None,
                is_dev=False,
            ),
        ],
        path=Path("."),
    )


class TestCheckCommand:
    """Tests for the check command."""

    def test_check_help(self) -> None:
        """Test check command help text."""
        result = runner.invoke(app, ["check", "--help"])
        assert result.exit_code == 0
        # Check for key content - options may be truncated in narrow terminals
        assert "check" in result.stdout.lower() or "dependencies" in result.stdout.lower()

    @patch("depswiz.cli.commands.check.scan_dependencies", new_callable=AsyncMock)
    def test_check_with_mock(
        self, mock_scan: AsyncMock, mock_check_result: CheckResult, tmp_path: Path
    ) -> None:
        """Test check command with mocked scanner."""
        mock_scan.return_value = mock_check_result

        result = runner.invoke(app, ["check", str(tmp_path)])
        assert result.exit_code == 0
        mock_scan.assert_called_once()

    @patch("depswiz.cli.commands.check.scan_dependencies", new_callable=AsyncMock)
    def test_check_json_format(
        self, mock_scan: AsyncMock, mock_check_result: CheckResult, tmp_path: Path
    ) -> None:
        """Test check command with JSON output format."""
        mock_scan.return_value = mock_check_result

        result = runner.invoke(app, ["check", "--format", "json", str(tmp_path)])
        assert result.exit_code == 0
        assert '"packages"' in result.stdout
        assert '"requests"' in result.stdout

    @patch("depswiz.cli.commands.check.scan_dependencies", new_callable=AsyncMock)
    def test_check_markdown_format(
        self, mock_scan: AsyncMock, mock_check_result: CheckResult, tmp_path: Path
    ) -> None:
        """Test check command with Markdown output format."""
        mock_scan.return_value = mock_check_result

        result = runner.invoke(app, ["check", "--format", "markdown", str(tmp_path)])
        assert result.exit_code == 0
        assert "# Dependency Report" in result.stdout

    @patch("depswiz.cli.commands.check.scan_dependencies", new_callable=AsyncMock)
    def test_check_fail_outdated_with_outdated(
        self, mock_scan: AsyncMock, mock_check_result: CheckResult, tmp_path: Path
    ) -> None:
        """Test check command fails when --fail-outdated and packages are outdated."""
        mock_scan.return_value = mock_check_result

        result = runner.invoke(app, ["check", "--fail-outdated", str(tmp_path)])
        # Should fail because requests is outdated
        assert result.exit_code == 1

    @patch("depswiz.cli.commands.check.scan_dependencies", new_callable=AsyncMock)
    def test_check_fail_outdated_when_up_to_date(
        self, mock_scan: AsyncMock, tmp_path: Path
    ) -> None:
        """Test check command succeeds when all packages are up to date."""
        up_to_date_result = CheckResult(
            packages=[
                Package(
                    name="httpx",
                    language="python",
                    constraint=">=0.25.0",
                    current_version="0.25.0",
                    latest_version="0.25.0",
                    update_type=None,
                    is_dev=False,
                ),
            ],
            path=Path("."),
        )
        mock_scan.return_value = up_to_date_result

        result = runner.invoke(app, ["check", "--fail-outdated", str(tmp_path)])
        assert result.exit_code == 0

    @patch("depswiz.cli.commands.check.scan_dependencies", new_callable=AsyncMock)
    def test_check_quiet_mode(
        self, mock_scan: AsyncMock, mock_check_result: CheckResult, tmp_path: Path
    ) -> None:
        """Test check command in quiet mode suppresses progress output."""
        mock_scan.return_value = mock_check_result

        result = runner.invoke(app, ["--quiet", "check", str(tmp_path)])
        assert result.exit_code == 0

    @patch("depswiz.cli.commands.check.scan_dependencies", new_callable=AsyncMock)
    def test_check_verbose_mode(
        self, mock_scan: AsyncMock, mock_check_result: CheckResult, tmp_path: Path
    ) -> None:
        """Test check command in verbose mode."""
        mock_scan.return_value = mock_check_result

        result = runner.invoke(app, ["--verbose", "check", str(tmp_path)])
        assert result.exit_code == 0


class TestCheckOutputFile:
    """Tests for check command output file option."""

    @patch("depswiz.cli.commands.check.scan_dependencies", new_callable=AsyncMock)
    def test_check_output_to_file(
        self, mock_scan: AsyncMock, mock_check_result: CheckResult, tmp_path: Path
    ) -> None:
        """Test check command writes output to file."""
        mock_scan.return_value = mock_check_result
        output_file = tmp_path / "output.json"

        result = runner.invoke(
            app, ["check", "--format", "json", "--output", str(output_file), str(tmp_path)]
        )
        assert result.exit_code == 0
        assert output_file.exists()
        content = output_file.read_text()
        assert '"packages"' in content


class TestCheckStrategy:
    """Tests for check command strategy filtering."""

    @patch("depswiz.cli.commands.check.scan_dependencies", new_callable=AsyncMock)
    def test_check_strategy_patch(
        self, mock_scan: AsyncMock, tmp_path: Path
    ) -> None:
        """Test check command with patch strategy."""
        result_with_major = CheckResult(
            packages=[
                Package(
                    name="pkg1",
                    language="python",
                    constraint=">=1.0.0",
                    current_version="1.0.0",
                    latest_version="2.0.0",
                    update_type=UpdateType.MAJOR,
                    is_dev=False,
                ),
                Package(
                    name="pkg2",
                    language="python",
                    constraint=">=1.0.0",
                    current_version="1.0.0",
                    latest_version="1.0.1",
                    update_type=UpdateType.PATCH,
                    is_dev=False,
                ),
            ],
            path=Path("."),
        )
        mock_scan.return_value = result_with_major

        result = runner.invoke(
            app, ["check", "--strategy", "patch", "--format", "json", str(tmp_path)]
        )
        assert result.exit_code == 0
        # Only patch updates should be shown
        assert "pkg2" in result.stdout
        # Major update should be filtered out
        assert "2.0.0" not in result.stdout

    @patch("depswiz.cli.commands.check.scan_dependencies", new_callable=AsyncMock)
    def test_check_strategy_minor(
        self, mock_scan: AsyncMock, tmp_path: Path
    ) -> None:
        """Test check command with minor strategy."""
        result_with_updates = CheckResult(
            packages=[
                Package(
                    name="pkg1",
                    language="python",
                    constraint=">=1.0.0",
                    current_version="1.0.0",
                    latest_version="2.0.0",
                    update_type=UpdateType.MAJOR,
                    is_dev=False,
                ),
                Package(
                    name="pkg2",
                    language="python",
                    constraint=">=1.0.0",
                    current_version="1.0.0",
                    latest_version="1.1.0",
                    update_type=UpdateType.MINOR,
                    is_dev=False,
                ),
            ],
            path=Path("."),
        )
        mock_scan.return_value = result_with_updates

        result = runner.invoke(
            app, ["check", "--strategy", "minor", "--format", "json", str(tmp_path)]
        )
        assert result.exit_code == 0
        # Minor update should be shown
        assert "pkg2" in result.stdout
