"""Main CLI application for depswiz."""

from pathlib import Path

import typer
from rich.console import Console

from depswiz import __version__
from depswiz.cli.commands import audit, check, licenses, plugins, sbom, suggest, tools, update

# Create the main app
app = typer.Typer(
    name="depswiz",
    help="Multi-language dependency wizard - check, audit, and update dependencies.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

# Create console for rich output
console = Console()

# Add subcommands
app.add_typer(check.app, name="check", help="Check for outdated dependencies")
app.add_typer(audit.app, name="audit", help="Scan for security vulnerabilities")
app.add_typer(licenses.app, name="licenses", help="Check license compliance")
app.add_typer(sbom.app, name="sbom", help="Generate Software Bill of Materials")
app.add_typer(update.app, name="update", help="Update dependencies")
app.add_typer(plugins.app, name="plugins", help="List and manage plugins")
app.add_typer(
    suggest.app, name="suggest", help="AI-powered upgrade suggestions (requires Claude Code)"
)
app.add_typer(tools.app, name="tools", help="Check development tools for updates")


@app.command()
def version() -> None:
    """Show version information."""
    console.print(f"[bold]depswiz[/bold] version [green]{__version__}[/green]")


@app.callback()
def main(
    ctx: typer.Context,
    config: Path | None = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to configuration file",
        exists=True,
        file_okay=True,
        dir_okay=False,
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Increase verbosity",
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        "-q",
        help="Suppress non-essential output",
    ),
    no_color: bool = typer.Option(
        False,
        "--no-color",
        help="Disable colored output",
    ),
) -> None:
    """depswiz - Multi-language dependency wizard.

    Check, audit, and update dependencies across Python, Rust, Dart, and JavaScript ecosystems.
    """
    # Store options in context for subcommands
    ctx.ensure_object(dict)
    ctx.obj["config_path"] = config
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet
    ctx.obj["no_color"] = no_color


if __name__ == "__main__":
    app()
