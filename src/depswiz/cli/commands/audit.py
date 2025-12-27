"""Audit command for depswiz."""

import asyncio
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from depswiz.cli.formatters import CliFormatter, HtmlFormatter, JsonFormatter, MarkdownFormatter
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
    severity: str = typer.Option(
        "low",
        "--severity",
        "-s",
        help="Minimum severity to report: low, medium, high, critical",
    ),
    ignore: list[str] | None = typer.Option(
        None,
        "--ignore",
        help="Ignore specific vulnerability ID (can be repeated)",
    ),
    ignore_file: Path | None = typer.Option(
        None,
        "--ignore-file",
        help="File with vulnerability IDs to ignore",
    ),
    fail_on: str = typer.Option(
        "high",
        "--fail-on",
        help="Exit with error at severity level: low, medium, high, critical",
    ),
    fix: bool = typer.Option(
        False,
        "--fix",
        help="Suggest fixes where available",
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
    """Scan dependencies for known vulnerabilities."""
    # Load configuration
    config_path = ctx.obj.get("config_path") if ctx.obj else None
    config = load_config(config_path, path)

    min_severity = parse_severity(severity)
    fail_severity = parse_severity(fail_on)

    # Collect ignored vulnerability IDs
    ignored_ids: set[str] = set()
    if ignore:
        ignored_ids.update(ignore)
    if ignore_file and ignore_file.exists():
        ignored_ids.update(
            line.strip()
            for line in ignore_file.read_text().splitlines()
            if line.strip() and not line.startswith("#")
        )

    ctx.obj.get("verbose", False) if ctx.obj else False
    quiet = ctx.obj.get("quiet", False) if ctx.obj else False

    # Run the scan and audit
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
                workspace=workspace or config.check.workspace,
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
    output_content = formatter.format_audit_result(audit_result, show_fix=fix)

    if output:
        output.write_text(output_content)
        if not quiet:
            console.print(f"[green]Output written to {output}[/green]")
    elif format_type == "cli":
        # CLI formatter already printed
        pass
    else:
        console.print(output_content)

    # Check if we should fail
    failing_vulns = [
        (pkg, vuln) for pkg, vuln in audit_result.vulnerabilities if vuln.severity >= fail_severity
    ]

    if failing_vulns:
        raise typer.Exit(code=1)
