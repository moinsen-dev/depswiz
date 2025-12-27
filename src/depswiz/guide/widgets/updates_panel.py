"""Updates panel widget for the guide dashboard."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.panel import Panel
from rich.table import Table
from textual.reactive import reactive
from textual.widget import Widget

if TYPE_CHECKING:
    from depswiz.core.models import CheckResult


class UpdatesPanel(Widget):
    """Panel showing outdated packages grouped by update type."""

    major_count: reactive[int] = reactive(0)
    minor_count: reactive[int] = reactive(0)
    patch_count: reactive[int] = reactive(0)
    is_loading: reactive[bool] = reactive(False)

    def render(self) -> Panel:
        """Render the updates panel."""
        if self.is_loading:
            return Panel("[italic]Scanning...[/italic]", title="Outdated Deps")

        table = Table(box=None, show_header=False, padding=(0, 1))
        table.add_column("Count", style="bold", width=3, justify="right")
        table.add_column("Type")

        # Add rows with appropriate colors
        if self.major_count > 0:
            table.add_row(str(self.major_count), "[red bold]Major[/red bold]")
        else:
            table.add_row("[dim]0[/dim]", "[dim]Major[/dim]")

        if self.minor_count > 0:
            table.add_row(str(self.minor_count), "[yellow]Minor[/yellow]")
        else:
            table.add_row("[dim]0[/dim]", "[dim]Minor[/dim]")

        if self.patch_count > 0:
            table.add_row(str(self.patch_count), "[blue]Patch[/blue]")
        else:
            table.add_row("[dim]0[/dim]", "[dim]Patch[/dim]")

        total = self.major_count + self.minor_count + self.patch_count
        border_style = "red" if self.major_count > 0 else ("yellow" if total > 0 else "green")

        return Panel(
            table,
            title=f"Outdated ({total})",
            border_style=border_style,
        )

    def update_from_result(self, result: CheckResult | None) -> None:
        """Update counts from a CheckResult."""
        if result:
            from depswiz.core.models import UpdateType

            self.major_count = sum(
                1 for p in result.outdated_packages if p.update_type == UpdateType.MAJOR
            )
            self.minor_count = sum(
                1 for p in result.outdated_packages if p.update_type == UpdateType.MINOR
            )
            self.patch_count = sum(
                1 for p in result.outdated_packages if p.update_type == UpdateType.PATCH
            )
        else:
            self.major_count = 0
            self.minor_count = 0
            self.patch_count = 0
