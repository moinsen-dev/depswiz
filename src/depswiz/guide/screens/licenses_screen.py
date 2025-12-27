"""Licenses details screen showing license compliance information."""

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


class LicensesScreen(ModalScreen):
    """Modal screen showing detailed license compliance information."""

    BINDINGS = [
        Binding("escape", "dismiss", "Close"),
        Binding("q", "dismiss", "Close"),
    ]

    CSS = """
    LicensesScreen {
        align: center middle;
    }

    #licenses-container {
        width: 90%;
        height: 90%;
        background: $surface;
        border: solid $primary;
        padding: 1;
    }

    #licenses-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    #licenses-content {
        height: 100%;
        overflow-y: auto;
    }
    """

    def __init__(self, state: GuideState) -> None:
        """Initialize the licenses screen.

        Args:
            state: Guide state with license results
        """
        super().__init__()
        self.state = state

    def compose(self) -> ComposeResult:
        """Compose the licenses screen layout."""
        with ScrollableContainer(id="licenses-container"):
            yield Static(self._render_title(), id="licenses-title")
            yield Static(self._render_content(), id="licenses-content")
        yield Footer()

    def _render_title(self) -> Text:
        """Render the screen title."""
        title = Text()
        title.append("License Compliance", style="bold")
        return title

    def _render_content(self) -> Table | Text:
        """Render the license compliance details."""
        if not self.state.license_result:
            return Text("No license data available. Press 'r' to scan.", style="dim")

        result = self.state.license_result
        violations = result.violations
        warnings = result.warnings

        if not violations and not warnings:
            return Text("All licenses are compliant! No issues found.", style="green")

        # Create combined table
        table = Table(
            title="License Issues",
            show_header=True,
            header_style="bold",
            expand=True,
        )
        table.add_column("Status", style="bold", width=12)
        table.add_column("Package", width=25)
        table.add_column("License", width=20)
        table.add_column("Reason", ratio=1)

        # Add violations first
        for violation in violations:
            table.add_row(
                Text("VIOLATION", style="red bold"),
                violation.package_name,
                violation.license_id or "Unknown",
                violation.reason or "License not allowed",
            )

        # Then warnings
        for warning in warnings:
            table.add_row(
                Text("WARNING", style="yellow"),
                warning.package_name,
                warning.license_id or "Unknown",
                warning.reason or "Review recommended",
            )

        return table

    def action_dismiss(self) -> None:
        """Close the screen."""
        self.app.pop_screen()
