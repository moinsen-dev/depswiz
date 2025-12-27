"""Tools details screen showing development tools status."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.table import Table
from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import ScrollableContainer
from textual.screen import ModalScreen
from textual.widgets import Footer, Static

if TYPE_CHECKING:
    from depswiz.guide.state import GuideState


class ToolsScreen(ModalScreen):
    """Modal screen showing detailed development tools information."""

    BINDINGS = [
        Binding("escape", "dismiss", "Close"),
        Binding("q", "dismiss", "Close"),
    ]

    CSS = """
    ToolsScreen {
        align: center middle;
    }

    #tools-container {
        width: 90%;
        height: 90%;
        background: $surface;
        border: solid $primary;
        padding: 1;
    }

    #tools-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    #tools-content {
        height: 100%;
        overflow-y: auto;
    }
    """

    def __init__(self, state: GuideState) -> None:
        """Initialize the tools screen.

        Args:
            state: Guide state with tools results
        """
        super().__init__()
        self.state = state

    def compose(self) -> ComposeResult:
        """Compose the tools screen layout."""
        with ScrollableContainer(id="tools-container"):
            yield Static(self._render_title(), id="tools-title")
            yield Static(self._render_content(), id="tools-content")
        yield Footer()

    def _render_title(self) -> Text:
        """Render the screen title."""
        title = Text()
        title.append("Development Tools", style="bold")
        return title

    def _render_content(self) -> Table | Text:
        """Render the tools details."""
        if not self.state.tools_result:
            return Text("No tools data available. Press 'r' to scan.", style="dim")

        tools = self.state.tools_result.tools
        if not tools:
            return Text("No development tools detected.", style="dim")

        table = Table(
            title=f"Found {len(tools)} Development Tools",
            show_header=True,
            header_style="bold",
            expand=True,
        )
        table.add_column("Tool", width=20)
        table.add_column("Current", width=15)
        table.add_column("Latest", width=15)
        table.add_column("Status", width=12)
        table.add_column("Path", ratio=1)

        for tool in tools:
            if tool.has_update:
                status = Text("Update", style="yellow")
            else:
                status = Text("OK", style="green")

            table.add_row(
                tool.name,
                str(tool.current_version) if tool.current_version else "N/A",
                str(tool.latest_version) if tool.latest_version else "N/A",
                status,
                str(tool.path) if tool.path else "",
            )

        return table

    def action_dismiss(self) -> None:
        """Close the screen."""
        self.app.pop_screen()
