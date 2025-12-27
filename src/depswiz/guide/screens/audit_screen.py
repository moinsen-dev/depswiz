"""Audit details screen showing vulnerability information."""

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


class AuditScreen(ModalScreen):
    """Modal screen showing detailed vulnerability information."""

    BINDINGS = [
        Binding("escape", "dismiss", "Close"),
        Binding("q", "dismiss", "Close"),
    ]

    CSS = """
    AuditScreen {
        align: center middle;
    }

    #audit-container {
        width: 90%;
        height: 90%;
        background: $surface;
        border: solid $primary;
        padding: 1;
    }

    #audit-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    #audit-content {
        height: 100%;
        overflow-y: auto;
    }

    .severity-critical {
        color: red;
        text-style: bold;
    }

    .severity-high {
        color: #ff8c00;
    }

    .severity-medium {
        color: yellow;
    }

    .severity-low {
        color: blue;
    }
    """

    def __init__(self, state: GuideState) -> None:
        """Initialize the audit screen.

        Args:
            state: Guide state with audit results
        """
        super().__init__()
        self.state = state

    def compose(self) -> ComposeResult:
        """Compose the audit screen layout."""
        with ScrollableContainer(id="audit-container"):
            yield Static(self._render_title(), id="audit-title")
            yield Static(self._render_content(), id="audit-content")
        yield Footer()

    def _render_title(self) -> Text:
        """Render the screen title."""
        title = Text()
        title.append("Security Vulnerabilities", style="bold")
        return title

    def _render_content(self) -> Table | Text:
        """Render the vulnerability details."""
        if not self.state.audit_result:
            return Text("No vulnerability data available. Press 'r' to scan.", style="dim")

        vulns = self.state.audit_result.vulnerabilities
        if not vulns:
            return Text("No vulnerabilities found! Your dependencies are secure.", style="green")

        table = Table(
            title=f"Found {len(vulns)} Vulnerabilities",
            show_header=True,
            header_style="bold",
            expand=True,
        )
        table.add_column("Severity", style="bold", width=10)
        table.add_column("Package", width=20)
        table.add_column("Version", width=12)
        table.add_column("CVE/ID", width=18)
        table.add_column("Title", ratio=1)
        table.add_column("Fixed In", width=12)

        # Sort by severity
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        sorted_vulns = sorted(
            vulns,
            key=lambda x: severity_order.get(str(x[1].severity).upper(), 4),
        )

        for pkg, vuln in sorted_vulns:
            severity = str(vuln.severity).upper()
            severity_style = {
                "CRITICAL": "red bold",
                "HIGH": "orange1",
                "MEDIUM": "yellow",
                "LOW": "blue",
            }.get(severity, "white")

            table.add_row(
                Text(severity, style=severity_style),
                pkg.name,
                str(pkg.current_version),
                vuln.id or "N/A",
                vuln.title[:40] + "..." if len(vuln.title) > 40 else vuln.title,
                vuln.fixed_version or "N/A",
            )

        return table

    def action_dismiss(self) -> None:
        """Close the screen."""
        self.app.pop_screen()
