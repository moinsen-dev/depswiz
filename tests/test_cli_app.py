"""Tests for the main CLI application."""

from typer.testing import CliRunner

from depswiz import __version__
from depswiz.cli.app import app

runner = CliRunner()


class TestVersionCommand:
    """Tests for the version command."""

    def test_version_command(self) -> None:
        """Test that version command shows version."""
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert __version__ in result.stdout

    def test_version_with_verbose(self) -> None:
        """Test version command with verbose flag."""
        result = runner.invoke(app, ["--verbose", "version"])
        assert result.exit_code == 0
        assert __version__ in result.stdout


class TestMainCallback:
    """Tests for the main callback options."""

    def test_help(self) -> None:
        """Test that help shows command descriptions."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "depswiz" in result.stdout
        assert "check" in result.stdout
        assert "audit" in result.stdout
        assert "tools" in result.stdout

    def test_verbose_flag(self) -> None:
        """Test verbose flag is accepted."""
        result = runner.invoke(app, ["--verbose", "version"])
        assert result.exit_code == 0

    def test_quiet_flag(self) -> None:
        """Test quiet flag is accepted."""
        result = runner.invoke(app, ["--quiet", "version"])
        assert result.exit_code == 0

    def test_no_color_flag(self) -> None:
        """Test no-color flag is accepted."""
        result = runner.invoke(app, ["--no-color", "version"])
        assert result.exit_code == 0

    def test_verbose_and_quiet_conflict(self) -> None:
        """Test that both verbose and quiet can be passed (quiet takes precedence)."""
        result = runner.invoke(app, ["--verbose", "--quiet", "version"])
        # Should succeed, quiet mode takes precedence in implementation
        assert result.exit_code == 0


class TestNoArgsIsHelp:
    """Test that no args shows help."""

    def test_no_args_shows_help(self) -> None:
        """Test that running with no args shows help."""
        result = runner.invoke(app, [])
        # no_args_is_help causes exit code 0 and shows help
        assert "Usage" in result.stdout or "depswiz" in result.stdout


class TestSubcommands:
    """Test that all subcommands are registered."""

    def test_check_help(self) -> None:
        """Test check command help."""
        result = runner.invoke(app, ["check", "--help"])
        assert result.exit_code == 0
        assert "dependencies" in result.stdout.lower() or "check" in result.stdout.lower()

    def test_audit_help(self) -> None:
        """Test audit command help."""
        result = runner.invoke(app, ["audit", "--help"])
        assert result.exit_code == 0
        assert "vulnerabilities" in result.stdout.lower() or "audit" in result.stdout.lower()

    def test_tools_help(self) -> None:
        """Test tools command help."""
        result = runner.invoke(app, ["tools", "--help"])
        assert result.exit_code == 0
        assert "tools" in result.stdout.lower()

    def test_licenses_help(self) -> None:
        """Test licenses command help."""
        result = runner.invoke(app, ["licenses", "--help"])
        assert result.exit_code == 0

    def test_sbom_help(self) -> None:
        """Test sbom command help."""
        result = runner.invoke(app, ["sbom", "--help"])
        assert result.exit_code == 0

    def test_plugins_help(self) -> None:
        """Test plugins command help."""
        result = runner.invoke(app, ["plugins", "--help"])
        assert result.exit_code == 0

    def test_suggest_help(self) -> None:
        """Test suggest command help."""
        result = runner.invoke(app, ["suggest", "--help"])
        assert result.exit_code == 0

    def test_update_help(self) -> None:
        """Test update command help."""
        result = runner.invoke(app, ["update", "--help"])
        assert result.exit_code == 0
