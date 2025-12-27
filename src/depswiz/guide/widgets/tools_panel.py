"""Tools panel widget for the guide dashboard."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.panel import Panel
from rich.table import Table
from textual.reactive import reactive
from textual.widget import Widget

if TYPE_CHECKING:
    from depswiz.tools.models import ToolsCheckResult


class ToolsPanel(Widget):
    """Panel showing development tools status."""

    tools: reactive[list] = reactive([])
    is_loading: reactive[bool] = reactive(False)

    def render(self) -> Panel:
        """Render the tools panel."""
        if self.is_loading:
            return Panel("[italic]Scanning...[/italic]", title="Development Tools")

        if not self.tools:
            return Panel("[dim]No tools detected[/dim]", title="Development Tools")

        table = Table(box=None, show_header=False, padding=(0, 1), expand=True)
        table.add_column("Tool", no_wrap=True)
        table.add_column("Version", no_wrap=True)
        table.add_column("Status", no_wrap=True, justify="right")

        outdated_count = 0
        for tool in self.tools[:6]:  # Limit display
            if tool.has_update:
                status = f"[yellow]↑ {tool.latest_version}[/yellow]"
                outdated_count += 1
            else:
                status = "[green]✓[/green]"

            table.add_row(tool.name, tool.current_version or "?", status)

        if len(self.tools) > 6:
            remaining = len(self.tools) - 6
            table.add_row("[dim]...[/dim]", f"[dim]+{remaining} more[/dim]", "")

        border_style = "yellow" if outdated_count > 0 else "green"
        title = f"Dev Tools ({len(self.tools)})"
        if outdated_count > 0:
            title += f" - {outdated_count} updates"

        return Panel(
            table,
            title=title,
            border_style=border_style,
        )

    def update_from_result(self, result: ToolsCheckResult | None) -> None:
        """Update from a ToolsCheckResult."""
        if result:
            self.tools = list(result.tools)
        else:
            self.tools = []
