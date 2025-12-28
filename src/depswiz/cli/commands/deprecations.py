"""Deprecation detection command for Flutter/Dart projects."""

from __future__ import annotations

import asyncio
from pathlib import Path

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

from depswiz.deprecations.models import Deprecation, DeprecationResult, DeprecationStatus
from depswiz.deprecations.scanner import apply_fixes, scan_deprecations

app = typer.Typer(invoke_without_command=True)
console = Console()


def _get_code_context(file_path: Path, line: int, context_lines: int = 5) -> str:
    """Get code context around a specific line.

    Args:
        file_path: Path to the source file
        line: Line number (1-indexed)
        context_lines: Number of lines before and after

    Returns:
        Code context as a string with line numbers
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            lines = f.readlines()

        start = max(0, line - context_lines - 1)
        end = min(len(lines), line + context_lines)

        context = []
        for i in range(start, end):
            marker = ">>> " if i == line - 1 else "    "
            context.append(f"{marker}{i + 1:4d} | {lines[i].rstrip()}")

        return "\n".join(context)
    except Exception:
        return f"(Could not read file: {file_path})"


def _run_ai_fix(
    deprecations: list[Deprecation],
    project_path: Path,
) -> tuple[bool, str]:
    """Run AI-powered deprecation fixing using Claude Code.

    Args:
        deprecations: List of deprecations to fix
        project_path: Project root path

    Returns:
        Tuple of (success, output_message)
    """
    from depswiz.ai.claude_client import ClaudeError, is_available, run_claude
    from depswiz.ai.prompts import get_deprecation_fix_prompt

    if not is_available():
        return False, (
            "Claude Code CLI not found.\n\n"
            "Install it from https://claude.ai/code\n"
            "Or use --fix for dart fix (limited to auto-fixable issues)."
        )

    # Build deprecation list for the prompt
    dep_list = []
    for dep in deprecations:
        try:
            rel_path = dep.file_path.relative_to(project_path)
        except ValueError:
            rel_path = dep.file_path
        dep_list.append({
            "file_path": str(rel_path),
            "line": dep.line,
            "column": dep.column,
            "message": dep.message,
            "rule_id": dep.rule_id,
            "replacement": dep.replacement,
        })

    # Generate the prompt
    prompt = get_deprecation_fix_prompt(dep_list)

    console.print("[dim]Sending deprecations to Claude Code for analysis and fixing...[/dim]")
    console.print(f"[dim]Processing {len(deprecations)} deprecation(s)...[/dim]")

    try:
        response = run_claude(prompt, timeout=600, cwd=project_path)
        return True, response
    except ClaudeError as e:
        return False, f"Claude Code error: {e}"
    except Exception as e:
        return False, f"Unexpected error: {e}"


@app.callback(invoke_without_command=True)
def deprecations(
    ctx: typer.Context,
    path: Path = typer.Argument(
        Path(),
        help="Project path to analyze",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    # Filtering
    fixable_only: bool = typer.Option(
        False,
        "--fixable-only",
        help="Show only auto-fixable deprecations",
    ),
    package: str | None = typer.Option(
        None,
        "--package",
        "-p",
        help="Filter by source package",
    ),
    status: str = typer.Option(
        "all",
        "--status",
        "-s",
        help="Filter by status: all, deprecated, removal, breaking",
    ),
    include_internal: bool = typer.Option(
        True,
        "--include-internal/--no-internal",
        help="Include deprecations from same package",
    ),
    # Output
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
    # Actions
    fix: bool = typer.Option(
        False,
        "--fix",
        help="Apply auto-fixes using dart fix",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Preview fixes without applying",
    ),
    ai_fix: bool = typer.Option(
        False,
        "--ai-fix",
        help="Use Claude Code for intelligent deprecation fixing",
    ),
    # CI
    fail_on: str | None = typer.Option(
        None,
        "--fail-on",
        help="Exit 1 if found: deprecated, removal, breaking",
    ),
) -> None:
    """Detect and fix deprecated API usage in Flutter/Dart projects.

    This command uses `dart analyze` to detect deprecated API usage
    and `dart fix` to automatically fix issues where possible.

    \b
    Examples:
      depswiz deprecations .                    # Scan current directory
      depswiz deprecations --fixable-only .     # Show only fixable issues
      depswiz deprecations --fix .              # Auto-fix deprecations
      depswiz deprecations --fix --dry-run .    # Preview fixes
      depswiz deprecations --format json .      # JSON output
      depswiz deprecations --fail-on breaking . # CI mode
    """
    project_path = path.resolve()

    # Check for pubspec.yaml
    if not (project_path / "pubspec.yaml").exists():
        console.print(
            Panel(
                "[red]No pubspec.yaml found.[/red]\n\n"
                "This command requires a Flutter/Dart project with pubspec.yaml.",
                title="Not a Dart Project",
                border_style="red",
            )
        )
        raise typer.Exit(1)

    # Run scan
    def progress(msg: str) -> None:
        console.print(f"[dim]{msg}[/dim]")

    result = asyncio.run(
        scan_deprecations(
            project_path,
            include_internal=include_internal,
            progress_callback=progress,
        )
    )

    # Apply filters
    filtered = _apply_filters(result, fixable_only, package, status)

    # Handle fix mode
    if fix or dry_run:
        success, output_msg = asyncio.run(
            apply_fixes(project_path, dry_run=dry_run, progress_callback=progress)
        )
        if success:
            console.print(Panel(output_msg, title="Fixes Applied" if not dry_run else "Fix Preview", border_style="green"))
        else:
            console.print(Panel(output_msg, title="Fix Failed", border_style="red"))
            raise typer.Exit(1)
        return

    # Handle AI fix mode
    if ai_fix:
        if not filtered:
            console.print(
                Panel(
                    "[green]No deprecations found![/green]\n\n"
                    "Nothing to fix - your code is up-to-date.",
                    title="All Clear",
                    border_style="green",
                )
            )
            return

        console.print()
        console.print(
            Panel(
                f"[bold]AI-Powered Deprecation Fixing[/bold]\n\n"
                f"Found [yellow]{len(filtered)}[/yellow] deprecation(s) to analyze.\n\n"
                "Claude Code will analyze each deprecation with full context and apply intelligent fixes.",
                title="depswiz + Claude Code",
                border_style="cyan",
            )
        )

        success, response = _run_ai_fix(filtered, project_path)

        if success:
            console.print()
            console.print(Panel(Markdown(response), title="Claude Code Response", border_style="green"))
            console.print()
            console.print("[dim]Re-run [cyan]depswiz deprecations[/cyan] to verify fixes.[/dim]")
        else:
            console.print(Panel(response, title="AI Fix Failed", border_style="red"))
            raise typer.Exit(1)
        return

    # Format output
    if format_type == "json":
        output_text = _format_json(result, filtered)
    elif format_type == "markdown":
        output_text = _format_markdown(result, filtered)
    elif format_type == "html":
        output_text = _format_html(result, filtered)
    else:
        _format_cli(result, filtered)
        output_text = None

    # Write to file if requested
    if output and output_text:
        output.write_text(output_text)
        console.print(f"[green]Output written to {output}[/green]")
    elif output_text:
        console.print(output_text)

    # Check fail-on condition
    if fail_on:
        exit_code = _check_fail_condition(filtered, fail_on)
        if exit_code:
            raise typer.Exit(exit_code)


def _apply_filters(
    result: DeprecationResult,
    fixable_only: bool,
    package: str | None,
    status: str,
) -> list:
    """Apply filters to deprecation results."""
    filtered = result.deprecations

    if fixable_only:
        filtered = [d for d in filtered if d.fix_available]

    if package:
        filtered = [d for d in filtered if d.package == package]

    if status != "all":
        status_map = {
            "deprecated": DeprecationStatus.DEPRECATED,
            "removal": DeprecationStatus.REMOVAL_PLANNED,
            "breaking": DeprecationStatus.BREAKING_SOON,
        }
        if status in status_map:
            min_status = status_map[status]
            filtered = [d for d in filtered if d.status >= min_status]

    return filtered


def _format_cli(result: DeprecationResult, filtered: list) -> None:
    """Format output for CLI display."""
    # Header
    console.print()
    console.print(
        Panel(
            f"[bold]depswiz deprecations[/bold] - {result.path.name}",
            border_style="blue",
        )
    )

    if not result.dart_version:
        console.print(
            Panel(
                "[yellow]Dart SDK not found.[/yellow]\n\n"
                "Please install Dart or Flutter to use this command.",
                title="SDK Not Found",
                border_style="yellow",
            )
        )
        return

    # Version info
    version_text = f"Dart {result.dart_version}"
    if result.flutter_version:
        version_text += f" | Flutter {result.flutter_version}"
    console.print(f"[dim]{version_text}[/dim]")
    console.print()

    if not filtered:
        console.print(
            Panel(
                "[green]No deprecations found![/green]\n\n"
                "Your code is up-to-date with current APIs.",
                title="All Clear",
                border_style="green",
            )
        )
        return

    # Summary tree
    summary = Tree("[bold]Summary[/bold]")
    summary.add(f"Total deprecations: [bold]{len(filtered)}[/bold]")
    summary.add(f"Auto-fixable: [bold]{result.fixable_count}[/bold] ({_pct(result.fixable_count, len(filtered))})")

    by_status = summary.add("By status:")
    for status, count in sorted(result.by_status.items(), key=lambda x: x[0].value):
        color = _status_color(status)
        by_status.add(f"[{color}]{status.value}[/{color}]: {count}")

    console.print(summary)
    console.print()

    # By package
    if result.by_package:
        pkg_tree = Tree("[bold]By Package[/bold]")
        for pkg, count in sorted(result.by_package.items(), key=lambda x: -x[1]):
            pkg_tree.add(f"{pkg}: {count}")
        console.print(pkg_tree)
        console.print()

    # Top issues table
    table = Table(title="Deprecations", show_header=True, header_style="bold")
    table.add_column("Status", style="dim", width=10)
    table.add_column("Location", style="cyan")
    table.add_column("Message", overflow="fold")
    table.add_column("Fix", width=5)

    for dep in filtered[:20]:  # Show first 20
        status_text = Text(dep.status.value, style=_status_color(dep.status))
        fix_text = Text("✓", style="green") if dep.fix_available else Text("-", style="dim")
        table.add_row(
            status_text,
            dep.short_location,
            dep.message[:80] + ("..." if len(dep.message) > 80 else ""),
            fix_text,
        )

    if len(filtered) > 20:
        table.add_row("", f"[dim]... and {len(filtered) - 20} more[/dim]", "", "")

    console.print(table)
    console.print()

    # Quick fix suggestions
    if result.fixable_count > 0 or len(filtered) > 0:
        fix_text_parts = []
        if result.fixable_count > 0:
            fix_text_parts.append(
                f"[bold]{result.fixable_count}[/bold] issues can be auto-fixed with dart fix:\n"
                f"  [cyan]depswiz deprecations --fix {result.path}[/cyan]\n"
                f"  [cyan]depswiz deprecations --fix --dry-run {result.path}[/cyan] (preview)"
            )
        if len(filtered) > 0:
            fix_text_parts.append(
                f"[bold]All {len(filtered)}[/bold] issues can be analyzed by Claude Code:\n"
                f"  [cyan]depswiz deprecations --ai-fix {result.path}[/cyan]"
            )
        console.print(
            Panel(
                "\n\n".join(fix_text_parts),
                title="Fix Options",
                border_style="green",
            )
        )


def _format_json(result: DeprecationResult, filtered: list) -> str:
    """Format output as JSON."""
    import json

    data = {
        "version": "0.5.0",
        "command": "deprecations",
        "timestamp": result.timestamp.isoformat(),
        "project": {
            "path": str(result.path),
            "dart_version": result.dart_version,
            "flutter_version": result.flutter_version,
        },
        "summary": {
            "total": len(filtered),
            "fixable": result.fixable_count,
            "by_status": {k.value: v for k, v in result.by_status.items()},
            "by_package": result.by_package,
        },
        "deprecations": [
            {
                "rule_id": d.rule_id,
                "message": d.message,
                "file": str(d.file_path),
                "line": d.line,
                "column": d.column,
                "status": d.status.value,
                "package": d.package,
                "replacement": d.replacement,
                "fix_available": d.fix_available,
                "references": d.references,
            }
            for d in filtered
        ],
    }
    return json.dumps(data, indent=2, default=str)


def _format_markdown(result: DeprecationResult, filtered: list) -> str:
    """Format output as Markdown."""
    lines = [
        f"# Deprecation Report: {result.path.name}",
        "",
        f"**Generated:** {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Dart Version:** {result.dart_version or 'N/A'}",
    ]
    if result.flutter_version:
        lines.append(f"**Flutter Version:** {result.flutter_version}")
    lines.append("")

    # Summary
    lines.extend([
        "## Summary",
        "",
        f"- **Total deprecations:** {len(filtered)}",
        f"- **Auto-fixable:** {result.fixable_count}",
        "",
        "### By Status",
        "",
        "| Status | Count |",
        "|--------|-------|",
    ])
    for status, count in sorted(result.by_status.items(), key=lambda x: x[0].value):
        lines.append(f"| {status.value} | {count} |")

    lines.extend(["", "### By Package", "", "| Package | Count |", "|---------|-------|"])
    for pkg, count in sorted(result.by_package.items(), key=lambda x: -x[1]):
        lines.append(f"| {pkg} | {count} |")

    # Details
    lines.extend(["", "## Deprecations", ""])
    for dep in filtered:
        lines.extend([
            f"### {dep.short_location}",
            "",
            f"- **Status:** {dep.status.value}",
            f"- **Rule:** `{dep.rule_id}`",
            f"- **Message:** {dep.message}",
        ])
        if dep.replacement:
            lines.append(f"- **Replacement:** `{dep.replacement}`")
        if dep.fix_available:
            lines.append("- **Auto-fixable:** Yes")
        lines.append("")

    return "\n".join(lines)


def _format_html(result: DeprecationResult, filtered: list) -> str:
    """Format output as HTML."""
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Deprecation Report - {result.path.name}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
               max-width: 1200px; margin: 0 auto; padding: 20px; background: #1a1a2e; color: #eee; }}
        h1, h2, h3 {{ color: #fff; }}
        .summary {{ display: flex; gap: 20px; flex-wrap: wrap; margin: 20px 0; }}
        .stat {{ background: #16213e; padding: 20px; border-radius: 8px; min-width: 150px; }}
        .stat-value {{ font-size: 2em; font-weight: bold; color: #0f4c75; }}
        .stat-label {{ color: #888; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #333; }}
        th {{ background: #16213e; }}
        .deprecated {{ color: #f39c12; }}
        .breaking {{ color: #e74c3c; }}
        .removal {{ color: #e74c3c; }}
        .info {{ color: #3498db; }}
        .fixable {{ color: #2ecc71; }}
    </style>
</head>
<body>
    <h1>Deprecation Report: {result.path.name}</h1>
    <p>Generated: {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>
    <p>Dart: {result.dart_version or 'N/A'} | Flutter: {result.flutter_version or 'N/A'}</p>

    <div class="summary">
        <div class="stat">
            <div class="stat-value">{len(filtered)}</div>
            <div class="stat-label">Total</div>
        </div>
        <div class="stat">
            <div class="stat-value fixable">{result.fixable_count}</div>
            <div class="stat-label">Fixable</div>
        </div>
        <div class="stat">
            <div class="stat-value breaking">{result.breaking_count}</div>
            <div class="stat-label">Breaking</div>
        </div>
    </div>

    <h2>Deprecations</h2>
    <table>
        <thead>
            <tr>
                <th>Status</th>
                <th>Location</th>
                <th>Message</th>
                <th>Fix</th>
            </tr>
        </thead>
        <tbody>
"""
    for dep in filtered:
        fix_icon = "✓" if dep.fix_available else "-"
        html += f"""            <tr>
                <td class="{dep.status.value}">{dep.status.value}</td>
                <td>{dep.short_location}</td>
                <td>{dep.message}</td>
                <td class="fixable">{fix_icon}</td>
            </tr>
"""
    html += """        </tbody>
    </table>
</body>
</html>
"""
    return html


def _status_color(status: DeprecationStatus) -> str:
    """Get Rich color for status."""
    colors = {
        DeprecationStatus.DEPRECATED: "yellow",
        DeprecationStatus.REMOVAL_PLANNED: "red",
        DeprecationStatus.BREAKING_SOON: "red bold",
        DeprecationStatus.INFO: "blue",
    }
    return colors.get(status, "white")


def _pct(part: int, total: int) -> str:
    """Calculate percentage string."""
    if total == 0:
        return "0%"
    return f"{int(part / total * 100)}%"


def _check_fail_condition(filtered: list, fail_on: str) -> int:
    """Check if any deprecation meets fail condition."""
    status_map = {
        "deprecated": DeprecationStatus.DEPRECATED,
        "removal": DeprecationStatus.REMOVAL_PLANNED,
        "breaking": DeprecationStatus.BREAKING_SOON,
    }
    if fail_on not in status_map:
        return 0

    min_status = status_map[fail_on]
    for dep in filtered:
        if dep.status >= min_status:
            return 1
    return 0
