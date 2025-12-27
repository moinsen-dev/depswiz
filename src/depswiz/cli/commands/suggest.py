"""Suggest command - AI-powered upgrade suggestions using Claude Code."""

import subprocess
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from depswiz.ai import claude_client
from depswiz.ai.prompts import get_prompt, list_prompts

app = typer.Typer(invoke_without_command=True)
console = Console()


@app.callback(invoke_without_command=True)
def suggest(
    ctx: typer.Context,
    path: Path = typer.Argument(
        Path("."),
        help="Project path to analyze",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    focus: str = typer.Option(
        "upgrade",
        "--focus",
        "-f",
        help="Analysis focus: upgrade, security, breaking, quick",
    ),
    timeout: int = typer.Option(
        300,
        "--timeout",
        "-t",
        help="Timeout in seconds for Claude response",
    ),
    raw: bool = typer.Option(
        False,
        "--raw",
        help="Output raw response without formatting",
    ),
) -> None:
    """Get AI-powered upgrade suggestions using Claude Code.

    This command leverages Claude Code CLI to analyze your project's
    dependencies and provide intelligent upgrade recommendations.

    Focus options:
    - upgrade: Full upgrade strategy with priorities and risks
    - security: Focus on security vulnerabilities
    - breaking: Analyze breaking changes in major updates
    - quick: Quick summary of dependency health

    Requires Claude Code CLI to be installed.
    Install from: https://claude.ai/code
    """
    # Check if Claude is available
    if not claude_client.is_available():
        console.print(
            Panel(
                "[yellow]Claude Code CLI not found.[/yellow]\n\n"
                "To use AI-powered suggestions, install Claude Code:\n"
                "[link=https://claude.ai/code]https://claude.ai/code[/link]\n\n"
                "After installation, run: [bold]claude --version[/bold]",
                title="Claude Code Required",
                border_style="yellow",
            )
        )
        raise typer.Exit(1)

    # Validate focus option
    valid_focuses = list_prompts()
    if focus not in valid_focuses:
        console.print(f"[red]Invalid focus: {focus}[/red]")
        console.print(f"Valid options: {', '.join(valid_focuses)}")
        raise typer.Exit(1)

    # Get the prompt for the requested focus
    prompt = get_prompt(focus)

    # Resolve the path
    project_path = path.resolve()

    console.print(f"\n[bold blue]depswiz suggest[/bold blue] - AI-Powered Analysis")
    console.print(f"Project: [cyan]{project_path}[/cyan]")
    console.print(f"Focus: [cyan]{focus}[/cyan]")
    console.print()

    try:
        with console.status(
            "[bold blue]Claude is analyzing your dependencies...[/bold blue]",
            spinner="dots",
        ):
            response = claude_client.run_claude(
                prompt,
                timeout=timeout,
                cwd=project_path,
            )

        # Display Claude's response
        console.print()
        if raw:
            console.print(response)
        else:
            console.print(
                Panel(
                    Markdown(response),
                    title="Claude's Analysis",
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
