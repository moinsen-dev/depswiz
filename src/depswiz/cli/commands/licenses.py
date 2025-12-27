"""Licenses command for depswiz."""

import asyncio
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from depswiz.cli.formatters import CliFormatter, HtmlFormatter, JsonFormatter, MarkdownFormatter
from depswiz.core.config import load_config
from depswiz.core.scanner import check_licenses, scan_dependencies

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
def licenses(
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
    policy: Path | None = typer.Option(
        None,
        "--policy",
        "-p",
        help="License policy file (TOML)",
    ),
    allow: list[str] | None = typer.Option(
        None,
        "--allow",
        help="Allow specific license (can be repeated)",
    ),
    deny: list[str] | None = typer.Option(
        None,
        "--deny",
        help="Deny specific license (can be repeated)",
    ),
    fail_on_unknown: bool = typer.Option(
        False,
        "--fail-on-unknown",
        help="Fail if license cannot be determined",
    ),
    summary: bool = typer.Option(
        False,
        "--summary",
        help="Show license summary only",
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
    """Check license compliance for dependencies."""
    # Load configuration
    config_path = ctx.obj.get("config_path") if ctx.obj else None
    config = load_config(config_path, path)

    # Override config with CLI options
    if allow:
        config.licenses.allowed = list(set(config.licenses.allowed + list(allow)))
    if deny:
        config.licenses.denied = list(set(config.licenses.denied + list(deny)))
    if fail_on_unknown:
        config.licenses.fail_on_unknown = True

    ctx.obj.get("verbose", False) if ctx.obj else False
    quiet = ctx.obj.get("quiet", False) if ctx.obj else False

    # Run the scan and license check
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        disable=quiet,
    ) as progress:
        # First scan for packages
        task = progress.add_task("Scanning dependencies...", total=None)
        check_result = asyncio.run(
            scan_dependencies(
                path=path,
                languages=language,
                recursive=recursive or config.check.recursive,
                workspace=config.check.workspace,
                include_dev=True,
                config=config,
                progress_callback=lambda msg: progress.update(task, description=msg),
            )
        )

        # Then check licenses
        progress.update(task, description="Checking licenses...")
        license_result = asyncio.run(
            check_licenses(
                packages=check_result.packages,
                config=config,
                progress_callback=lambda msg: progress.update(task, description=msg),
            )
        )

        progress.update(task, description="Done!")

    # Format and output results
    formatter = get_formatter(format_type)
    output_content = formatter.format_license_result(license_result, summary_only=summary)

    if output:
        output.write_text(output_content)
        if not quiet:
            console.print(f"[green]Output written to {output}[/green]")
    elif format_type == "cli":
        # CLI formatter already printed
        pass
    else:
        console.print(output_content)

    # Exit with error if violations found
    if license_result.has_violations:
        raise typer.Exit(code=1)
