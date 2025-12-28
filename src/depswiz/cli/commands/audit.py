"""Audit command for depswiz."""

import asyncio
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from depswiz.cli.context import determine_format, is_ci_environment, parse_language_filter
from depswiz.cli.formatters import CliFormatter, HtmlFormatter, JsonFormatter, MarkdownFormatter, SarifFormatter
from depswiz.core.config import load_config
from depswiz.core.models import Severity
from depswiz.core.scanner import audit_packages, scan_dependencies

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


def parse_severity(value: str) -> Severity:
    """Parse a severity string into a Severity enum."""
    try:
        return Severity[value.upper()]
    except KeyError as err:
        raise typer.BadParameter(
            f"Invalid severity: {value}. Must be one of: low, medium, high, critical"
        ) from err


@app.callback(invoke_without_command=True)
def audit(
    ctx: typer.Context,
    path: Path = typer.Argument(
        Path(),
        help="Project path to audit",
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
    # Severity filter
    severity: str = typer.Option(
        "low",
        "--severity",
        "-s",
        help="Minimum severity to report: low, medium, high, critical",
    ),
    # Unified strict mode (replaces --fail-on)
    strict: str | None = typer.Option(
        None,
        "--strict",
        help="Exit with error at severity: low, medium, high, critical (auto-enabled at 'high' in CI)",
    ),
    # Ignore specific vulnerabilities
    ignore: list[str] | None = typer.Option(
        None,
        "--ignore",
        help="Ignore specific vulnerability ID (can be repeated)",
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
    """Scan dependencies for known vulnerabilities.

    By default, scans the entire project recursively and reports all severities.

    Examples:
        depswiz audit                     # Audit everything
        depswiz audit --severity high     # Only high/critical
        depswiz audit --strict            # Fail on high+ (default in CI)
        depswiz audit --json -o audit.json
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

    min_severity = parse_severity(severity)

    # Strict mode: explicit flag, or auto 'high' in CI
    if strict is not None:
        fail_severity = parse_severity(strict)
        use_strict = True
    elif in_ci:
        fail_severity = Severity.HIGH
        use_strict = True
    else:
        fail_severity = Severity.HIGH
        use_strict = False

    # Collect ignored vulnerability IDs
    ignored_ids: set[str] = set()
    if ignore:
        ignored_ids.update(ignore)

    quiet = ctx.obj.get("quiet", False) if ctx.obj else False

    # Run the scan and audit
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

        # Then audit for vulnerabilities
        progress.update(task, description="Checking vulnerabilities...")
        audit_result = asyncio.run(
            audit_packages(
                packages=check_result.packages,
                config=config,
                progress_callback=lambda msg: progress.update(task, description=msg),
            )
        )

        progress.update(task, description="Done!")

    # Filter by severity and ignored IDs
    filtered_vulns = [
        (pkg, vuln)
        for pkg, vuln in audit_result.vulnerabilities
        if vuln.severity >= min_severity and vuln.id not in ignored_ids
    ]
    audit_result.vulnerabilities = filtered_vulns

    # Format and output results
    formatter = get_formatter(format_type)
    output_content = formatter.format_audit_result(audit_result, show_fix=True)

    if output:
        output.write_text(output_content)
        if not quiet and format_type == "cli":
            console.print(f"[green]Output written to {output}[/green]")
    elif format_type == "cli":
        # CLI formatter already printed
        pass
    else:
        console.print(output_content)

    # Check if we should fail
    if use_strict:
        failing_vulns = [
            (pkg, vuln)
            for pkg, vuln in audit_result.vulnerabilities
            if vuln.severity >= fail_severity
        ]
        if failing_vulns:
            raise typer.Exit(code=1)
