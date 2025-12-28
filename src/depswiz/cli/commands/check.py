"""Check command for depswiz."""

import asyncio
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from depswiz.cli.context import determine_format, is_ci_environment, parse_language_filter
from depswiz.cli.formatters import CliFormatter, HtmlFormatter, JsonFormatter, MarkdownFormatter, SarifFormatter
from depswiz.core.config import load_config
from depswiz.core.models import CheckResult, UpdateType
from depswiz.core.scanner import scan_dependencies

app = typer.Typer(invoke_without_command=True)
console = Console()


def get_formatter(format_type: str):
    """Get the appropriate formatter for the output format."""
    formatters = {
        "cli": CliFormatter(console),
        "json": JsonFormatter(),
        "markdown": MarkdownFormatter(),
        "html": HtmlFormatter(),
        "sarif": SarifFormatter(),
    }
    return formatters.get(format_type, formatters["cli"])


@app.callback(invoke_without_command=True)
def check(
    ctx: typer.Context,
    path: Path = typer.Argument(
        Path(),
        help="Project path to check",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    # Simplified language filter
    only: str | None = typer.Option(
        None,
        "--only",
        help="Only check specific languages (comma-separated, e.g., python,docker)",
    ),
    # Recursive is now TRUE by default, --shallow to opt-out
    shallow: bool = typer.Option(
        False,
        "--shallow",
        help="Only scan current directory (don't recurse)",
    ),
    # Simplified dev dependency handling
    prod: bool = typer.Option(
        False,
        "--prod",
        help="Exclude development dependencies",
    ),
    # Unified strict mode
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
    sarif_output: bool = typer.Option(
        False,
        "--sarif",
        help="Output as SARIF (for GitHub Code Scanning, VS Code)",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Write output to file",
    ),
    # Strategy for filtering updates
    strategy: str = typer.Option(
        "all",
        "--strategy",
        "-s",
        help="Update strategy: all, patch, minor, major",
        hidden=True,  # Less commonly used, hide from main help
    ),
) -> None:
    """Check dependencies for available updates.

    By default, scans the entire project recursively for all supported languages.

    Examples:
        depswiz check                    # Check everything
        depswiz check --only python      # Only Python
        depswiz check --shallow          # Just current directory
        depswiz check --json -o out.json # JSON output to file
    """
    # Load configuration
    config_path = ctx.obj.get("config_path") if ctx.obj else None
    config = load_config(config_path, path)

    # Determine if we're in CI - affects defaults
    in_ci = is_ci_environment()

    # Recursive is TRUE by default now
    recursive = not shallow

    # Parse language filter
    languages = parse_language_filter(only)

    # Determine format (with CI auto-detection)
    format_type = determine_format(json_output, md_output, html_output, sarif_output)
    if in_ci and format_type == "cli" and not any([json_output, md_output, html_output, sarif_output]):
        # In CI, default to JSON if no format specified
        format_type = "json"

    # Strict mode: explicit flag, or auto in CI
    use_strict = strict if strict is not None else in_ci

    # Dev dependencies: include unless --prod
    include_dev = not prod

    quiet = ctx.obj.get("quiet", False) if ctx.obj else False

    # Run the scan
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        disable=quiet or format_type != "cli",
    ) as progress:
        task = progress.add_task("Scanning dependencies...", total=None)

        result = asyncio.run(
            scan_dependencies(
                path=path,
                languages=languages,
                recursive=recursive,
                workspace=True,  # Always detect workspaces
                include_dev=include_dev,
                config=config,
                progress_callback=lambda msg: progress.update(task, description=msg),
            )
        )

        progress.update(task, description="Done!")

    # Filter by strategy
    if strategy != "all":
        result = filter_by_strategy(result, strategy)

    # Format and output results
    formatter = get_formatter(format_type)
    output_content = formatter.format_check_result(result, warn_breaking=True)

    if output:
        output.write_text(output_content)
        if not quiet and format_type == "cli":
            console.print(f"[green]Output written to {output}[/green]")
    elif format_type == "cli":
        # CLI formatter already printed
        pass
    else:
        console.print(output_content)

    # Exit with error if strict mode and outdated packages found
    if use_strict and result.outdated_packages:
        raise typer.Exit(code=1)


def filter_by_strategy(result: CheckResult, strategy: str) -> CheckResult:
    """Filter packages based on update strategy."""
    if strategy == "all":
        return result

    strategy_map = {
        "patch": [UpdateType.PATCH],
        "minor": [UpdateType.PATCH, UpdateType.MINOR],
        "major": [UpdateType.PATCH, UpdateType.MINOR, UpdateType.MAJOR],
    }

    allowed_types = strategy_map.get(strategy, [])
    if not allowed_types:
        return result

    filtered_packages = [
        pkg
        for pkg in result.packages
        if pkg.update_type is None or pkg.update_type in allowed_types
    ]

    return CheckResult(
        packages=filtered_packages,
        timestamp=result.timestamp,
        path=result.path,
    )
