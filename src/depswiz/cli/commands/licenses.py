"""Licenses command for depswiz."""

import asyncio
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from depswiz.cli.context import determine_format, is_ci_environment, parse_language_filter
from depswiz.cli.formatters import CliFormatter, HtmlFormatter, JsonFormatter, MarkdownFormatter, SarifFormatter
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
        "sarif": SarifFormatter(),
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
    # License policy
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
    # Unified strict mode
    strict: bool | None = typer.Option(
        None,
        "--strict",
        help="Exit with error if violations found (auto-enabled in CI)",
    ),
    # Summary only mode
    summary: bool = typer.Option(
        False,
        "--summary",
        help="Show license summary only",
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
) -> None:
    """Check license compliance for dependencies.

    By default, scans the entire project recursively and checks all licenses.

    Examples:
        depswiz licenses                   # Check all licenses
        depswiz licenses --deny GPL-3.0    # Deny GPL-3.0
        depswiz licenses --summary         # Just show counts
        depswiz licenses --json -o lic.json
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
        format_type = "json"

    # Strict mode: explicit flag, or auto in CI
    use_strict = strict if strict is not None else in_ci

    # Override config with CLI options
    if allow:
        config.licenses.allowed = list(set(config.licenses.allowed + list(allow)))
    if deny:
        config.licenses.denied = list(set(config.licenses.denied + list(deny)))

    quiet = ctx.obj.get("quiet", False) if ctx.obj else False

    # Run the scan and license check
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        disable=quiet or format_type != "cli",
    ) as progress:
        # First scan for packages
        task = progress.add_task("Scanning dependencies...", total=None)
        check_result = asyncio.run(
            scan_dependencies(
                path=path,
                languages=languages,
                recursive=recursive,
                workspace=True,  # Always detect workspaces
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
        if not quiet and format_type == "cli":
            console.print(f"[green]Output written to {output}[/green]")
    elif format_type == "cli":
        # CLI formatter already printed
        pass
    else:
        console.print(output_content)

    # Exit with error if strict mode and violations found
    if use_strict and license_result.has_violations:
        raise typer.Exit(code=1)
