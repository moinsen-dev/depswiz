"""Main CLI application for depswiz."""

import asyncio
from pathlib import Path

import typer
from rich.console import Console

from depswiz import __version__
from depswiz.cli.commands import (
    audit,
    check,
    deprecations,
    guide,
    licenses,
    plugins,
    sbom,
    suggest,
    tools,
    update,
)
from depswiz.cli.context import determine_format, is_ci_environment, parse_language_filter
from depswiz.cli.formatters import CliFormatter, JsonFormatter
from depswiz.core.config import load_config
from depswiz.core.logging import LogLevel, setup_logging
from depswiz.core.scanner import audit_packages, check_licenses, scan_dependencies

# Create the main app - no_args_is_help=False so we can run default scan
app = typer.Typer(
    name="depswiz",
    help="Multi-language dependency wizard - check, audit, and update dependencies.",
    no_args_is_help=False,
    invoke_without_command=True,
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
app.add_typer(
    guide.app, name="guide", help="Interactive dependency guide (TUI, wizard, or chat)"
)
app.add_typer(
    deprecations.app,
    name="deprecations",
    help="Detect and fix deprecated API usage (Flutter/Dart)",
)


@app.command()
def version() -> None:
    """Show version information."""
    console.print(f"[bold]depswiz[/bold] version [green]{__version__}[/green]")


def _version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"depswiz {__version__}")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    path: Path = typer.Option(
        None,
        "--path",
        "-p",
        help="Project path to scan (default: current directory)",
    ),
    show_version: bool = typer.Option(
        False,
        "--version",
        "-V",
        help="Show version and exit",
        callback=_version_callback,
        is_eager=True,
    ),
    config: Path | None = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to configuration file",
        exists=True,
        file_okay=True,
        dir_okay=False,
    ),
    # Simplified options for default scan
    only: str | None = typer.Option(
        None,
        "--only",
        help="Only check specific languages (comma-separated)",
    ),
    shallow: bool = typer.Option(
        False,
        "--shallow",
        help="Only scan current directory (don't recurse)",
    ),
    prod: bool = typer.Option(
        False,
        "--prod",
        help="Exclude development dependencies",
    ),
    strict: bool | None = typer.Option(
        None,
        "--strict",
        help="Exit with error if issues found (auto-enabled in CI)",
    ),
    # Format shortcuts
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output as JSON",
    ),
    md_output: bool = typer.Option(
        False,
        "--md",
        help="Output as Markdown",
    ),
    html_output: bool = typer.Option(
        False,
        "--html",
        help="Output as HTML",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Write output to file",
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

    Run without a subcommand to perform a comprehensive scan:
    outdated dependencies, security vulnerabilities, and license compliance.

    Examples:
        depswiz                       # Full scan of current project
        depswiz -p /path/to/project   # Scan specific project
        depswiz --only python         # Only Python dependencies
        depswiz --json -o scan.json

    Or use specific commands:
        depswiz check     # Just check for outdated dependencies
        depswiz audit     # Just scan for vulnerabilities
        depswiz licenses  # Just check license compliance
    """
    # Store options in context for subcommands
    ctx.ensure_object(dict)
    ctx.obj["config_path"] = config
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet
    ctx.obj["no_color"] = no_color

    # Configure logging based on verbosity flags
    if quiet:
        setup_logging(LogLevel.QUIET, rich_output=not no_color)
    elif verbose:
        setup_logging(LogLevel.VERBOSE, rich_output=not no_color)
    else:
        setup_logging(LogLevel.NORMAL, rich_output=not no_color)

    # If a subcommand was invoked, let it handle everything
    if ctx.invoked_subcommand is not None:
        return

    # No subcommand - run comprehensive scan
    run_comprehensive_scan(
        path=path or Path(),
        config_path=config,
        only=only,
        shallow=shallow,
        prod=prod,
        strict=strict,
        json_output=json_output,
        md_output=md_output,
        html_output=html_output,
        output=output,
        quiet=quiet,
    )


def run_comprehensive_scan(
    path: Path,
    config_path: Path | None,
    only: str | None,
    shallow: bool,
    prod: bool,
    strict: bool | None,
    json_output: bool,
    md_output: bool,
    html_output: bool,
    output: Path | None,
    quiet: bool,
) -> None:
    """Run a comprehensive scan: outdated + vulnerabilities + licenses."""
    from rich.progress import Progress, SpinnerColumn, TextColumn

    # Validate path
    if not path.exists():
        console.print(f"[red]Error: Path does not exist: {path}[/red]")
        raise typer.Exit(code=1)

    # Load configuration
    cfg = load_config(config_path, path)

    # Determine if we're in CI
    in_ci = is_ci_environment()

    # Parse options
    recursive = not shallow
    languages = parse_language_filter(only)
    include_dev = not prod

    # Determine format
    format_type = determine_format(json_output, md_output, html_output)
    if in_ci and format_type == "cli" and not any([json_output, md_output, html_output]):
        format_type = "json"

    # Strict mode
    use_strict = strict if strict is not None else in_ci

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        disable=quiet or format_type != "cli",
    ) as progress:
        # 1. Scan dependencies
        task = progress.add_task("Scanning dependencies...", total=None)
        check_result = asyncio.run(
            scan_dependencies(
                path=path,
                languages=languages,
                recursive=recursive,
                workspace=True,
                include_dev=include_dev,
                config=cfg,
                progress_callback=lambda msg: progress.update(task, description=msg),
            )
        )

        # 2. Audit for vulnerabilities
        progress.update(task, description="Checking vulnerabilities...")
        audit_result = asyncio.run(
            audit_packages(
                packages=check_result.packages,
                config=cfg,
                progress_callback=lambda msg: progress.update(task, description=msg),
            )
        )

        # 3. Check licenses
        progress.update(task, description="Checking licenses...")
        license_result = asyncio.run(
            check_licenses(
                packages=check_result.packages,
                config=cfg,
                progress_callback=lambda msg: progress.update(task, description=msg),
            )
        )

        progress.update(task, description="Done!")

    # Format output
    if format_type == "json":
        formatter = JsonFormatter()
        output_content = formatter.format_comprehensive_scan(
            check_result, audit_result, license_result
        )
    else:
        formatter = CliFormatter(console)
        output_content = formatter.format_comprehensive_scan(
            check_result, audit_result, license_result
        )

    if output:
        output.write_text(output_content)
        if not quiet and format_type == "cli":
            console.print(f"[green]Output written to {output}[/green]")
    elif format_type != "cli":
        console.print(output_content)

    # Exit with error if strict and issues found
    if use_strict:
        has_issues = (
            len(check_result.outdated_packages) > 0
            or len(audit_result.vulnerabilities) > 0
            or license_result.has_violations
        )
        if has_issues:
            raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
