"""Update command for depswiz."""

import asyncio
import subprocess
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm
from rich.table import Table

from depswiz.cli.context import parse_language_filter
from depswiz.core.config import load_config
from depswiz.core.models import UpdateType
from depswiz.core.scanner import scan_dependencies
from depswiz.plugins import get_plugin

app = typer.Typer(invoke_without_command=True)
console = Console()


@app.callback(invoke_without_command=True)
def update(
    ctx: typer.Context,
    path: Path = typer.Argument(
        Path(),
        help="Project path to update",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    # Simplified language filter
    only: str | None = typer.Option(
        None,
        "--only",
        help="Only update specific languages (comma-separated, e.g., python,docker)",
    ),
    # Update strategy
    strategy: str = typer.Option(
        "minor",
        "--strategy",
        "-s",
        help="Update strategy: all, security, patch, minor, major",
    ),
    # Specific packages
    package: list[str] | None = typer.Option(
        None,
        "--package",
        "-p",
        help="Update specific package only (can be repeated)",
    ),
    # Control options
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be updated without making changes",
    ),
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Skip confirmation prompts",
    ),
    no_lockfile: bool = typer.Option(
        False,
        "--no-lockfile",
        help="Don't update lockfiles",
    ),
) -> None:
    """Update dependencies interactively.

    By default, scans the entire project recursively and proposes
    minor and patch updates.

    Examples:
        depswiz update                  # Interactive update
        depswiz update --strategy patch # Only patch updates
        depswiz update --dry-run        # Preview changes
        depswiz update -y               # Skip confirmation
        depswiz update -p requests      # Update specific package
    """
    # Load configuration
    config_path = ctx.obj.get("config_path") if ctx.obj else None
    config = load_config(config_path, path)

    # Parse language filter
    languages = parse_language_filter(only)

    verbose = ctx.obj.get("verbose", False) if ctx.obj else False
    quiet = ctx.obj.get("quiet", False) if ctx.obj else False

    # Run the scan - recursive by default
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        disable=quiet,
    ) as progress:
        task = progress.add_task("Scanning dependencies...", total=None)

        check_result = asyncio.run(
            scan_dependencies(
                path=path,
                languages=languages,
                recursive=True,  # Always scan recursively
                workspace=True,  # Always detect workspaces
                include_dev=True,
                config=config,
                progress_callback=lambda msg: progress.update(task, description=msg),
            )
        )

        progress.update(task, description="Done!")

    # Filter outdated packages
    outdated = check_result.outdated_packages

    # Filter by strategy
    if strategy != "all":
        strategy_map = {
            "patch": [UpdateType.PATCH],
            "minor": [UpdateType.PATCH, UpdateType.MINOR],
            "major": [UpdateType.PATCH, UpdateType.MINOR, UpdateType.MAJOR],
        }
        allowed_types = strategy_map.get(strategy, [])
        outdated = [p for p in outdated if p.update_type in allowed_types]

    # Filter by specific packages
    if package:
        package_set = set(package)
        outdated = [p for p in outdated if p.name in package_set]

    if not outdated:
        console.print("[green]All dependencies are up to date![/green]")
        return

    # Show what will be updated
    table = Table(title="Proposed Updates")
    table.add_column("Package", style="cyan")
    table.add_column("Language", style="magenta")
    table.add_column("Current", style="yellow")
    table.add_column("Latest", style="green")
    table.add_column("Type", style="blue")

    for pkg in outdated:
        update_type_str = str(pkg.update_type) if pkg.update_type else "unknown"
        table.add_row(
            pkg.display_name,
            pkg.language or "unknown",
            pkg.current_version or "?",
            pkg.latest_version or "?",
            update_type_str,
        )

    console.print(table)

    if dry_run:
        console.print("\n[yellow]Dry run - no changes made[/yellow]")
        return

    # Confirm updates
    if not yes:
        if not Confirm.ask("\nProceed with updates?"):
            console.print("[yellow]Update cancelled[/yellow]")
            return

    # Group packages by language
    packages_by_language: dict[str, list] = {}
    for pkg in outdated:
        lang = pkg.language or "unknown"
        if lang not in packages_by_language:
            packages_by_language[lang] = []
        packages_by_language[lang].append(pkg)

    # Generate and execute update commands
    for lang, packages in packages_by_language.items():
        plugin = get_plugin(lang)
        if plugin is None:
            console.print(f"[yellow]No plugin for {lang}, skipping[/yellow]")
            continue

        commands = plugin.generate_update_command(packages, include_lockfile=not no_lockfile)

        for cmd in commands:
            console.print(f"\n[bold]Running:[/bold] {cmd}")

            try:
                result = subprocess.run(
                    cmd,
                    shell=True,
                    cwd=path,
                    capture_output=True,
                    text=True,
                )

                if result.returncode == 0:
                    console.print("[green]Success[/green]")
                    if verbose and result.stdout:
                        console.print(result.stdout)
                else:
                    console.print(f"[red]Failed (exit code {result.returncode})[/red]")
                    if result.stderr:
                        console.print(result.stderr)

            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")

    console.print("\n[green]Updates complete![/green]")
