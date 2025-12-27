"""Updates details screen showing outdated packages."""

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


class UpdatesScreen(ModalScreen):
    """Modal screen showing detailed outdated packages information."""

    BINDINGS = [
        Binding("escape", "dismiss", "Close"),
        Binding("q", "dismiss", "Close"),
    ]

    CSS = """
    UpdatesScreen {
        align: center middle;
    }

    #updates-container {
        width: 90%;
        height: 90%;
        background: $surface;
        border: solid $primary;
        padding: 1;
    }

    #updates-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    #updates-content {
        height: 100%;
        overflow-y: auto;
    }

    .update-major {
        color: red;
        text-style: bold;
    }

    .update-minor {
        color: yellow;
    }

    .update-patch {
        color: green;
    }
    """

    def __init__(self, state: GuideState) -> None:
        """Initialize the updates screen.

        Args:
            state: Guide state with check results
        """
        super().__init__()
        self.state = state

    def compose(self) -> ComposeResult:
        """Compose the updates screen layout."""
        with ScrollableContainer(id="updates-container"):
            yield Static(self._render_title(), id="updates-title")
            yield Static(self._render_content(), id="updates-content")
        yield Footer()

    def _render_title(self) -> Text:
        """Render the screen title."""
        title = Text()
        title.append("Outdated Dependencies", style="bold")
        return title

    def _render_content(self) -> Table | Text:
        """Render the outdated packages details."""
        if not self.state.check_result:
            return Text("No dependency data available. Press 'r' to scan.", style="dim")

        outdated = self.state.check_result.outdated_packages
        if not outdated:
            return Text("All dependencies are up to date!", style="green")

        from depswiz.core.models import UpdateType

        table = Table(
            title=f"Found {len(outdated)} Outdated Packages",
            show_header=True,
            header_style="bold",
            expand=True,
        )
        table.add_column("Type", style="bold", width=8)
        table.add_column("Package", width=25)
        table.add_column("Current", width=12)
        table.add_column("Latest", width=12)
        table.add_column("Language", width=12)

        # Sort by update type (major first)
        type_order = {UpdateType.MAJOR: 0, UpdateType.MINOR: 1, UpdateType.PATCH: 2}
        sorted_pkgs = sorted(
            outdated,
            key=lambda x: type_order.get(x.update_type, 3),
        )

        for pkg in sorted_pkgs:
            update_type = pkg.update_type
            type_style = {
                UpdateType.MAJOR: "red bold",
                UpdateType.MINOR: "yellow",
                UpdateType.PATCH: "green",
            }.get(update_type, "white")

            type_label = {
                UpdateType.MAJOR: "MAJOR",
                UpdateType.MINOR: "MINOR",
                UpdateType.PATCH: "PATCH",
            }.get(update_type, "???")

            table.add_row(
                Text(type_label, style=type_style),
                pkg.name,
                str(pkg.current_version),
                str(pkg.latest_version),
                pkg.language or "unknown",
            )

        return table

    def action_dismiss(self) -> None:
        """Close the screen."""
        self.app.pop_screen()
