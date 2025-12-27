"""Tools command - check development tools for updates."""

import asyncio
import json
import subprocess
from pathlib import Path

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from depswiz import __version__
from depswiz.ai import claude_client
from depswiz.tools import scan_tools
from depswiz.tools.definitions import get_all_tool_names
from depswiz.tools.models import ToolStatus

app = typer.Typer(invoke_without_command=True)
console = Console()


def _run_async(coro):
    """Run an async coroutine synchronously."""
    return asyncio.run(coro)


@app.callback(invoke_without_command=True)
def tools(
    ctx: typer.Context,
    path: Path = typer.Argument(
        Path(),
        help="Project path for auto-detection",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    tool: list[str] | None = typer.Option(
        None,
        "--tool",
        "-t",
        help="Specific tool(s) to check (can be repeated)",
    ),
    all_tools: bool = typer.Option(
        False,
        "--all",
        "-a",
        help="Check all supported tools",
    ),
    updates_only: bool = typer.Option(
        False,
        "--updates-only",
        "-u",
        help="Only show tools with available updates",
    ),
    show_instructions: bool = typer.Option(
        True,
        "--instructions/--no-instructions",
        help="Show update instructions",
    ),
    include_not_installed: bool = typer.Option(
        False,
        "--include-not-installed",
        help="Include tools that are not installed",
    ),
    format_type: str = typer.Option(
        "cli",
        "--format",
        "-f",
        help="Output format: cli, json",
    ),
    list_supported: bool = typer.Option(
        False,
        "--list",
        "-l",
        help="List all supported tools",
    ),
    upgrade: bool = typer.Option(
        False,
        "--upgrade",
        "--update",
        help="Use Claude Code to perform intelligent upgrades",
    ),
    timeout: int = typer.Option(
        300,
        "--timeout",
        help="Timeout in seconds for Claude response (used with --upgrade)",
    ),
) -> None:
    """Check development tools for updates.

    By default, auto-detects relevant tools based on project files.
    Use --all to check all supported tools.
    Use -t/--tool to check specific tools.
    Use --upgrade to have Claude Code perform the updates intelligently.

    Examples:
        depswiz tools                     # Auto-detect and check
        depswiz tools --all               # Check all tools
        depswiz tools -t node -t python   # Check specific tools
        depswiz tools --updates-only      # Only show updates
        depswiz tools --format json       # JSON output
        depswiz tools --upgrade           # Use Claude to upgrade tools
    """
    # Handle list flag
    if list_supported:
        all_names = get_all_tool_names()
        console.print(f"\n[bold]Supported Tools ({len(all_names)}):[/bold]\n")
        for name in sorted(all_names):
            console.print(f"  • {name}")
        console.print()
        return

    # Resolve path
    project_path = path.resolve()

    # Run the async scan
    result = _run_async(
        scan_tools(
            path=project_path,
            tool_names=tool,
            check_all=all_tools,
            include_not_installed=include_not_installed,
        )
    )

    # Filter to updates only if requested
    if updates_only:
        result.tools = [t for t in result.tools if t.status == ToolStatus.UPDATE_AVAILABLE]

    # JSON output
    if format_type == "json":
        console.print(json.dumps(result.to_dict(), indent=2))
        return

    # CLI output
    console.print(f"\n[bold blue]depswiz[/bold blue] v{__version__} - Development Tools Check")
    console.print(f"Platform: [cyan]{result.platform.value}[/cyan]")
    console.print()

    if not result.tools:
        console.print("[yellow]No tools detected or specified.[/yellow]")
        console.print("Use --all to check all supported tools, or -t to specify tools.")
        return

    # Create table
    table = Table(show_header=True, header_style="bold")
    table.add_column("Tool", style="cyan")
    table.add_column("Installed")
    table.add_column("Latest")
    table.add_column("Status")

    for t in result.tools:
        # Format installed version
        if t.current_version:
            installed = str(t.current_version)
        elif t.status == ToolStatus.NOT_INSTALLED:
            installed = "[dim]not installed[/dim]"
        else:
            installed = "[dim]unknown[/dim]"

        # Format latest version
        if t.latest_version:
            latest = str(t.latest_version)
        else:
            latest = "[dim]unknown[/dim]"

        # Format status
        if t.status == ToolStatus.UP_TO_DATE:
            status = "[green]✓ up to date[/green]"
        elif t.status == ToolStatus.UPDATE_AVAILABLE:
            status = "[yellow]↑ update available[/yellow]"
        elif t.status == ToolStatus.NOT_INSTALLED:
            status = "[dim]not installed[/dim]"
        else:
            status = f"[red]error: {t.error_message}[/red]"

        table.add_row(t.display_name, installed, latest, status)

    console.print(table)
    console.print()

    # Summary
    if result.updates_available > 0:
        console.print(f"[yellow]{result.updates_available} update(s) available[/yellow]")
    else:
        console.print("[green]All tools are up to date![/green]")

    # Show update instructions if there are updates
    if show_instructions and result.updates_available > 0 and not upgrade:
        console.print()
        console.print("[bold]Update Instructions:[/bold]")
        for t in result.tools:
            if t.status == ToolStatus.UPDATE_AVAILABLE and t.update_instruction:
                console.print(f"  [cyan]{t.display_name}:[/cyan] {t.update_instruction}")

    # Handle upgrade mode with Claude Code
    if upgrade and result.updates_available > 0:
        console.print()

        # Check if Claude is available
        if not claude_client.is_available():
            console.print(
                Panel(
                    "[yellow]Claude Code CLI not found.[/yellow]\n\n"
                    "To use AI-powered upgrades, install Claude Code:\n"
                    "[link=https://claude.ai/code]https://claude.ai/code[/link]\n\n"
                    "After installation, run: [bold]claude --version[/bold]",
                    title="Claude Code Required",
                    border_style="yellow",
                )
            )
            raise typer.Exit(1)

        # Build upgrade prompt with detected tool info
        tools_info = []
        for t in result.tools:
            if t.status == ToolStatus.UPDATE_AVAILABLE:
                tools_info.append(
                    f"- {t.display_name}: {t.current_version} → {t.latest_version}"
                    f" (suggested: {t.update_instruction})"
                )

        upgrade_prompt = f"""
The following development tools need to be updated on this {result.platform.value} system:

{chr(10).join(tools_info)}

Please update these tools one by one. For each tool:
1. Run the appropriate upgrade command
2. Verify the upgrade succeeded by checking the version
3. Report any issues or warnings

Use the suggested commands as guidance, but feel free to use alternative methods if they are more appropriate (e.g., using version managers like nvm, rustup, etc.).

Important: Execute the upgrade commands and verify results. Report back on what was updated successfully and any issues encountered.
"""

        try:
            with console.status(
                "[bold blue]Claude is upgrading your development tools...[/bold blue]",
                spinner="dots",
            ):
                response = claude_client.run_claude(
                    upgrade_prompt,
                    timeout=timeout,
                    cwd=project_path,
                )

            # Display Claude's response
            console.print()
            console.print(
                Panel(
                    Markdown(response),
                    title="Claude's Upgrade Report",
                    border_style="green",
                )
            )

        except subprocess.TimeoutExpired:
            console.print(
                f"[red]Claude timed out after {timeout} seconds.[/red]\n"
                "Try increasing the timeout with --timeout"
            )
            raise typer.Exit(1)

        except claude_client.ClaudeError as e:
            console.print(f"[red]Claude error: {e}[/red]")
            raise typer.Exit(1)

        except Exception as e:
            console.print(f"[red]Unexpected error: {e}[/red]")
            raise typer.Exit(1)
