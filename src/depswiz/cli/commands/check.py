"""Check command for depswiz."""

import asyncio
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from depswiz.cli.formatters import CliFormatter, HtmlFormatter, JsonFormatter, MarkdownFormatter
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
    language: list[str] | None = typer.Option(
        None,
        "--language",
        "-l",
        help="Filter by language (can be repeated)",
    ),
    recursive: bool = typer.Option(
        False,
        "--recursive",
        "-r",
        help="Scan subdirectories",
    ),
    workspace: bool = typer.Option(
        False,
        "--workspace",
        "-w",
        help="Detect and scan workspaces",
    ),
    include_dev: bool = typer.Option(
        True,
        "--include-dev/--no-dev",
        help="Include development dependencies",
    ),
    strategy: str = typer.Option(
        "all",
        "--strategy",
        "-s",
        help="Update strategy: all, security, patch, minor, major",
    ),
    warn_breaking: bool = typer.Option(
        True,
        "--warn-breaking/--no-warn-breaking",
        help="Warn about breaking changes",
    ),
    fail_outdated: bool = typer.Option(
        False,
        "--fail-outdated",
        help="Exit with error if outdated packages found",
    ),
    format_type: str = typer.Option(
        "cli",
        "--format",
        "-f",
        help="Output format: cli, json, markdown, html",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Write output to file",
    ),
) -> None:
    """Check dependencies for available updates."""
    # Load configuration
    config_path = ctx.obj.get("config_path") if ctx.obj else None
    config = load_config(config_path, path)

    # Override config with CLI options
    if recursive:
        config.check.recursive = recursive
    if workspace:
        config.check.workspace = workspace

    ctx.obj.get("verbose", False) if ctx.obj else False
    quiet = ctx.obj.get("quiet", False) if ctx.obj else False

    # Run the scan
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        disable=quiet,
    ) as progress:
        task = progress.add_task("Scanning dependencies...", total=None)

        result = asyncio.run(
            scan_dependencies(
                path=path,
                languages=language,
                recursive=config.check.recursive,
                workspace=config.check.workspace,
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
    output_content = formatter.format_check_result(result, warn_breaking=warn_breaking)

    if output:
        output.write_text(output_content)
        if not quiet:
            console.print(f"[green]Output written to {output}[/green]")
    elif format_type == "cli":
        # CLI formatter already printed
        pass
    else:
        console.print(output_content)

    # Exit with error if configured and outdated packages found
    if fail_outdated and result.outdated_packages:
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
