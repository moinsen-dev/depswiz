"""Plugins command for depswiz."""

import typer
from rich.console import Console
from rich.table import Table

from depswiz.plugins.registry import get_plugin, list_plugins

app = typer.Typer()
console = Console()


@app.command("list")
def list_cmd() -> None:
    """List all available plugins."""
    plugins_info = list_plugins()

    if not plugins_info:
        console.print("[yellow]No plugins installed[/yellow]")
        return

    table = Table(title="Installed Plugins")
    table.add_column("Name", style="cyan")
    table.add_column("Display Name", style="green")
    table.add_column("Manifest Patterns")
    table.add_column("Lockfile Patterns")
    table.add_column("Workspaces", style="magenta")

    for info in plugins_info:
        table.add_row(
            info["name"],
            info["display_name"],
            ", ".join(info["manifest_patterns"]),
            ", ".join(info["lockfile_patterns"]),
            "Yes" if info["supports_workspaces"] else "No",
        )

    console.print(table)


@app.command("info")
def info_cmd(
    name: str = typer.Argument(..., help="Plugin name"),
) -> None:
    """Show detailed information about a plugin."""
    plugin = get_plugin(name)

    if plugin is None:
        console.print(f"[red]Plugin '{name}' not found[/red]")
        raise typer.Exit(code=1)

    console.print(f"\n[bold]{plugin.display_name}[/bold] ({plugin.name})")
    console.print("\n[cyan]Manifest files:[/cyan]")
    for pattern in plugin.manifest_patterns:
        console.print(f"  - {pattern}")

    console.print("\n[cyan]Lockfile files:[/cyan]")
    for pattern in plugin.lockfile_patterns:
        console.print(f"  - {pattern}")

    console.print(f"\n[cyan]OSV Ecosystem:[/cyan] {plugin.ecosystem}")
    console.print(
        f"[cyan]Workspace support:[/cyan] {'Yes' if plugin.supports_workspaces() else 'No'}"
    )
