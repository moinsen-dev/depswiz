"""Welcome/introduction screen explaining depswiz features."""

from __future__ import annotations

from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import ScrollableContainer
from textual.screen import ModalScreen
from textual.widgets import Footer, Static


class WelcomeScreen(ModalScreen):
    """Welcome screen with tool introduction and keyboard shortcuts.

    Provides comprehensive information about depswiz features,
    dashboard panels, keyboard shortcuts, and getting started tips.
    """

    BINDINGS = [
        Binding("escape", "dismiss", "Close"),
        Binding("q", "dismiss", "Close"),
    ]

    CSS = """
    WelcomeScreen {
        align: center middle;
    }

    #welcome-container {
        width: 90%;
        height: 90%;
        background: $surface;
        border: solid $primary;
        padding: 1 2;
    }

    #welcome-content {
        height: 100%;
        overflow-y: auto;
    }

    .section-title {
        text-style: bold;
        color: $primary;
        margin-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose the welcome screen layout."""
        with ScrollableContainer(id="welcome-container"):
            yield Static(self._render_content(), id="welcome-content")
        yield Footer()

    def _render_content(self) -> Group:
        """Render all welcome screen content."""
        sections = [
            self._render_header(),
            self._render_what_is(),
            self._render_dashboard_panels(),
            self._render_shortcuts(),
            self._render_languages(),
            self._render_quickstart(),
            self._render_footer(),
        ]
        return Group(*sections)

    def _render_header(self) -> Panel:
        """Render the header/title section."""
        title = Text()
        title.append("depswiz guide\n", style="bold cyan")
        title.append("Your Interactive Dependency Dashboard", style="dim")
        return Panel(
            title,
            border_style="cyan",
            padding=(1, 2),
        )

    def _render_what_is(self) -> Panel:
        """Render the 'What is depswiz?' section."""
        content = Text()
        content.append("depswiz", style="bold")
        content.append(" is a comprehensive dependency management tool that helps you:\n\n")
        content.append("  * ", style="cyan")
        content.append("Check for outdated packages across Python, Rust, Dart, JS, and Docker\n")
        content.append("  * ", style="cyan")
        content.append("Scan for security vulnerabilities\n")
        content.append("  * ", style="cyan")
        content.append("Verify license compliance\n")
        content.append("  * ", style="cyan")
        content.append("Monitor development tool versions\n")
        content.append("  * ", style="cyan")
        content.append("Get AI-powered upgrade suggestions")

        return Panel(
            content,
            title="[bold]What is depswiz?[/bold]",
            border_style="green",
            padding=(0, 1),
        )

    def _render_dashboard_panels(self) -> Panel:
        """Render the dashboard panels explanation."""
        panels_table = Table(show_header=False, box=None, padding=(0, 1))
        panels_table.add_column("Panel", style="bold", width=14)
        panels_table.add_column("Description")

        panels_table.add_row(
            "[green]HEALTH SCORE[/green]",
            "Your overall project health (0-100). Based on vulnerabilities, "
            "outdated deps, and license violations. Higher is better!",
        )
        panels_table.add_row(
            "[red]VULNERABILITIES[/red]",
            "Security vulnerabilities found in your dependencies. "
            "Grouped by severity: Critical, High, Medium, Low.",
        )
        panels_table.add_row(
            "[yellow]OUTDATED DEPS[/yellow]",
            "Packages with available updates. Categorized as Major, Minor, or Patch updates.",
        )
        panels_table.add_row(
            "[blue]LICENSES[/blue]",
            "License compliance status. Shows compliance %, violations, and warnings.",
        )
        panels_table.add_row(
            "[cyan]TOOLS[/cyan]",
            "Development tool versions (Node, Python, Rust, etc.). "
            "Shows current vs latest available versions.",
        )

        return Panel(
            panels_table,
            title="[bold]Dashboard Panels[/bold]",
            border_style="blue",
            padding=(0, 1),
        )

    def _render_shortcuts(self) -> Panel:
        """Render the keyboard shortcuts table."""
        shortcuts_table = Table(
            show_header=True,
            header_style="bold",
            box=None,
            padding=(0, 1),
        )
        shortcuts_table.add_column("Key", style="bold cyan", width=6)
        shortcuts_table.add_column("Action")

        shortcuts = [
            ("r", "Refresh - Rescan the project"),
            ("a", "Audit - View detailed vulnerability information"),
            ("u", "Updates - View all outdated packages"),
            ("l", "Licenses - View license compliance details"),
            ("t", "Tools - View development tool status"),
            ("c", "Chat - Open conversational interface"),
            ("s", "AI Suggest - Get AI-powered recommendations"),
            ("?", "Help - Show this welcome screen"),
            ("q", "Quit - Exit depswiz guide"),
        ]

        for key, action in shortcuts:
            shortcuts_table.add_row(key, action)

        return Panel(
            shortcuts_table,
            title="[bold]Keyboard Shortcuts[/bold]",
            border_style="magenta",
            padding=(0, 1),
        )

    def _render_languages(self) -> Panel:
        """Render the supported languages section."""
        languages = Text()
        langs = ["Python", "Rust", "Dart/Flutter", "JavaScript/TypeScript", "Docker"]
        for i, lang in enumerate(langs):
            if i > 0:
                languages.append(" * ", style="dim")
            languages.append(lang, style="bold")

        return Panel(
            languages,
            title="[bold]Supported Languages[/bold]",
            border_style="yellow",
            padding=(0, 1),
        )

    def _render_quickstart(self) -> Panel:
        """Render the quick start section."""
        content = Text()
        steps = [
            "The dashboard auto-scans your project on startup",
            "Press 'a', 'u', 'l', or 't' to drill into details",
            "Press 's' for AI-powered upgrade suggestions",
            "Press 'r' to rescan after making changes",
        ]

        for i, step in enumerate(steps, 1):
            content.append(f"  {i}. ", style="bold cyan")
            content.append(f"{step}\n")

        return Panel(
            content,
            title="[bold]Quick Start[/bold]",
            border_style="green",
            padding=(0, 1),
        )

    def _render_footer(self) -> Text:
        """Render the footer with dismiss instruction."""
        footer = Text()
        footer.append("\n")
        footer.append("Press ", style="dim")
        footer.append("ESC", style="bold")
        footer.append(" or ", style="dim")
        footer.append("q", style="bold")
        footer.append(" to close", style="dim")
        return footer

    def action_dismiss(self) -> None:
        """Close the screen."""
        self.app.pop_screen()
