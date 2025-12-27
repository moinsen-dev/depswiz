"""Main Textual application for the guide TUI dashboard."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import Footer, Header, Static
from textual.worker import get_current_worker

from depswiz.guide.screens import (
    AIScreen,
    AuditScreen,
    ChatScreen,
    LicensesScreen,
    ToolsScreen,
    UpdatesScreen,
)

if TYPE_CHECKING:
    from depswiz.core.config import Config
    from depswiz.guide.context import ContextManager
    from depswiz.guide.state import GuideState


class GuideApp(App):
    """Main depswiz guide TUI application.

    Provides a real-time dashboard showing:
    - Overall health score
    - Vulnerability status
    - Outdated dependencies
    - License compliance
    - Development tools status
    """

    CSS = """
    Screen {
        layout: grid;
        grid-size: 3 3;
        grid-gutter: 1;
        padding: 1;
    }

    #health-container {
        row-span: 2;
        border: solid green;
        padding: 1;
    }

    #vulns-container {
        border: solid red;
        padding: 1;
    }

    #updates-container {
        border: solid yellow;
        padding: 1;
    }

    #licenses-container {
        border: solid blue;
        padding: 1;
    }

    #tools-container {
        column-span: 2;
        border: solid cyan;
        padding: 1;
    }

    .panel-title {
        text-style: bold;
        margin-bottom: 1;
    }

    .score-display {
        text-align: center;
        height: 100%;
    }

    .score-value {
        text-style: bold;
    }

    .status-good {
        color: green;
    }

    .status-warning {
        color: yellow;
    }

    .status-error {
        color: red;
    }

    #status-bar {
        dock: bottom;
        height: 1;
        background: $surface;
        padding: 0 1;
    }

    .scanning {
        text-style: italic;
        color: $text-muted;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("a", "show_audit", "Audit Details"),
        Binding("u", "show_updates", "Update Details"),
        Binding("l", "show_licenses", "License Details"),
        Binding("t", "show_tools", "Tools Details"),
        Binding("c", "toggle_chat", "Chat"),
        Binding("s", "ai_suggest", "AI Suggest"),
        Binding("?", "show_help", "Help"),
    ]

    TITLE = "depswiz guide"

    def __init__(
        self,
        path: Path,
        config: Config,
        state: GuideState,
        watch: bool = False,
        context_manager: ContextManager | None = None,
    ):
        """Initialize the guide app.

        Args:
            path: Project path to analyze
            config: depswiz configuration
            state: Shared guide state
            watch: Whether to watch for file changes
            context_manager: Optional context manager for AI features
        """
        super().__init__()
        self.project_path = path
        self.config = config
        self.state = state
        self.watch_mode = watch
        self._context_manager = context_manager

        # Subscribe to state changes
        self.state.subscribe(self._on_state_change)

    @property
    def context_manager(self) -> ContextManager:
        """Get or create the context manager."""
        if self._context_manager is None:
            from depswiz.guide.context import ContextManager

            self._context_manager = ContextManager(self.project_path, self.config)
        return self._context_manager

    def compose(self) -> ComposeResult:
        """Compose the app layout."""
        yield Header()

        # Health score panel
        yield Container(
            Static("HEALTH SCORE", classes="panel-title"),
            Static(self._render_health_score(), id="health-score"),
            id="health-container",
        )

        # Vulnerabilities panel
        yield Container(
            Static("VULNERABILITIES", classes="panel-title"),
            Static(self._render_vulns(), id="vulns-content"),
            id="vulns-container",
        )

        # Updates panel
        yield Container(
            Static("OUTDATED DEPS", classes="panel-title"),
            Static(self._render_updates(), id="updates-content"),
            id="updates-container",
        )

        # Licenses panel
        yield Container(
            Static("LICENSES", classes="panel-title"),
            Static(self._render_licenses(), id="licenses-content"),
            id="licenses-container",
        )

        # Tools panel
        yield Container(
            Static("DEVELOPMENT TOOLS", classes="panel-title"),
            Static(self._render_tools(), id="tools-content"),
            id="tools-container",
        )

        # Status bar
        yield Static(self._render_status(), id="status-bar")

        yield Footer()

    async def on_mount(self) -> None:
        """Start initial scan when app mounts."""
        self.run_full_scan()

    def _on_state_change(self, state: GuideState) -> None:
        """Handle state changes and refresh UI."""
        self.call_from_thread(self._refresh_panels)

    def _refresh_panels(self) -> None:
        """Refresh all dashboard panels."""
        try:
            self.query_one("#health-score", Static).update(self._render_health_score())
            self.query_one("#vulns-content", Static).update(self._render_vulns())
            self.query_one("#updates-content", Static).update(self._render_updates())
            self.query_one("#licenses-content", Static).update(self._render_licenses())
            self.query_one("#tools-content", Static).update(self._render_tools())
            self.query_one("#status-bar", Static).update(self._render_status())
        except Exception:
            pass  # Widget might not exist yet

    def _render_health_score(self) -> str:
        """Render the health score display."""
        if self.state.is_scanning:
            return "[italic]Scanning...[/italic]"

        score = self.state.health_score
        status = self.state.health_status
        color = self.state.health_color

        return f"""
[{color} bold]{score}[/{color} bold]
/100

[{color}]{status}[/{color}]
"""

    def _render_vulns(self) -> str:
        """Render vulnerabilities panel content."""
        if self.state.is_scanning:
            return "[italic]Scanning...[/italic]"

        if not self.state.audit_result:
            return "[dim]No data[/dim]"

        lines = []
        if self.state.critical_count > 0:
            lines.append(f"[red bold]{self.state.critical_count}[/red bold] Critical")
        else:
            lines.append("[dim]0 Critical[/dim]")

        if self.state.high_count > 0:
            lines.append(f"[orange1 bold]{self.state.high_count}[/orange1 bold] High")
        else:
            lines.append("[dim]0 High[/dim]")

        if self.state.medium_count > 0:
            lines.append(f"[yellow]{self.state.medium_count}[/yellow] Medium")
        else:
            lines.append("[dim]0 Medium[/dim]")

        if self.state.low_count > 0:
            lines.append(f"[blue]{self.state.low_count}[/blue] Low")
        else:
            lines.append("[dim]0 Low[/dim]")

        return "\n".join(lines)

    def _render_updates(self) -> str:
        """Render updates panel content."""
        if self.state.is_scanning:
            return "[italic]Scanning...[/italic]"

        if not self.state.check_result:
            return "[dim]No data[/dim]"

        breakdown = self.state.update_breakdown
        lines = []

        if breakdown["major"] > 0:
            lines.append(f"[red bold]{breakdown['major']}[/red bold] Major")
        else:
            lines.append("[dim]0 Major[/dim]")

        if breakdown["minor"] > 0:
            lines.append(f"[yellow]{breakdown['minor']}[/yellow] Minor")
        else:
            lines.append("[dim]0 Minor[/dim]")

        if breakdown["patch"] > 0:
            lines.append(f"[blue]{breakdown['patch']}[/blue] Patch")
        else:
            lines.append("[dim]0 Patch[/dim]")

        return "\n".join(lines)

    def _render_licenses(self) -> str:
        """Render licenses panel content."""
        if self.state.is_scanning:
            return "[italic]Scanning...[/italic]"

        if not self.state.license_result:
            return "[dim]No data[/dim]"

        pct = self.state.license_compliance_pct
        violations = self.state.violation_count
        warnings = self.state.warning_count

        if pct >= 100:
            color = "green"
        elif pct >= 90:
            color = "yellow"
        else:
            color = "red"

        lines = [f"[{color} bold]{pct}%[/{color} bold] Compliant"]

        if violations > 0:
            lines.append(f"[red]{violations}[/red] Violations")
        if warnings > 0:
            lines.append(f"[yellow]{warnings}[/yellow] Warnings")

        return "\n".join(lines)

    def _render_tools(self) -> str:
        """Render tools panel content."""
        if self.state.is_scanning:
            return "[italic]Scanning...[/italic]"

        if not self.state.tools_result:
            return "[dim]No data[/dim]"

        lines = []
        for tool in self.state.tools_result.tools[:6]:  # Limit display
            if tool.has_update:
                status = f"[yellow]↑ {tool.latest_version}[/yellow]"
            else:
                status = "[green]✓[/green]"

            lines.append(f"{tool.name} {tool.current_version} {status}")

        if len(self.state.tools_result.tools) > 6:
            remaining = len(self.state.tools_result.tools) - 6
            lines.append(f"[dim]... and {remaining} more[/dim]")

        return "\n".join(lines) if lines else "[dim]No tools detected[/dim]"

    def _render_status(self) -> str:
        """Render status bar content."""
        if self.state.is_scanning:
            return f"[italic]{self.state.scan_progress or 'Scanning...'}[/italic]"

        if self.state.last_scan_time:
            age = datetime.now() - self.state.last_scan_time
            if age.total_seconds() < 60:
                age_str = "just now"
            elif age.total_seconds() < 3600:
                age_str = f"{int(age.total_seconds() / 60)} min ago"
            else:
                age_str = f"{int(age.total_seconds() / 3600)} hr ago"
            return f"Last scan: {age_str} | Press [bold]?[/bold] for help"

        return "Press [bold]r[/bold] to scan | [bold]?[/bold] for help"

    def run_full_scan(self) -> None:
        """Run all scans in background."""
        self.run_worker(self._do_full_scan(), exclusive=True)

    async def _do_full_scan(self) -> None:
        """Execute full project scan."""
        from depswiz.core.scanner import (
            audit_packages,
            check_licenses,
            scan_dependencies,
        )
        from depswiz.tools.scanner import scan_tools

        worker = get_current_worker()
        self.state.is_scanning = True
        self.state.notify()

        try:
            # Scan dependencies
            self.state.scan_progress = "Scanning dependencies..."
            self.state.notify()

            self.state.check_result = await scan_dependencies(
                path=self.project_path,
                config=self.config,
            )

            if worker.is_cancelled:
                return

            # Audit for vulnerabilities
            self.state.scan_progress = "Checking vulnerabilities..."
            self.state.notify()

            if self.state.check_result:
                self.state.audit_result = await audit_packages(
                    packages=self.state.check_result.packages,
                    config=self.config,
                )

            if worker.is_cancelled:
                return

            # Check licenses
            self.state.scan_progress = "Verifying licenses..."
            self.state.notify()

            if self.state.check_result:
                self.state.license_result = await check_licenses(
                    packages=self.state.check_result.packages,
                    config=self.config,
                )

            if worker.is_cancelled:
                return

            # Check dev tools
            self.state.scan_progress = "Checking development tools..."
            self.state.notify()

            self.state.tools_result = await scan_tools(path=self.project_path)

            self.state.last_scan_time = datetime.now()

        except Exception as e:
            self.state.errors.append(str(e))
        finally:
            self.state.is_scanning = False
            self.state.scan_progress = ""
            self.state.notify()

    def action_refresh(self) -> None:
        """Handle refresh action."""
        self.run_full_scan()

    def action_show_audit(self) -> None:
        """Show detailed audit screen."""
        self.push_screen(AuditScreen(self.state))

    def action_show_updates(self) -> None:
        """Show detailed updates screen."""
        self.push_screen(UpdatesScreen(self.state))

    def action_show_licenses(self) -> None:
        """Show detailed licenses screen."""
        self.push_screen(LicensesScreen(self.state))

    def action_show_tools(self) -> None:
        """Show detailed tools screen."""
        self.push_screen(ToolsScreen(self.state))

    def action_toggle_chat(self) -> None:
        """Toggle chat panel."""
        self.push_screen(ChatScreen(self.state, self.context_manager))

    def action_ai_suggest(self) -> None:
        """Get AI suggestions."""
        self.push_screen(AIScreen(self.state, self.context_manager))

    def action_show_help(self) -> None:
        """Show help screen."""
        self.notify(
            "r=Refresh, a=Audit, u=Updates, l=Licenses, t=Tools, c=Chat, s=AI, q=Quit",
            severity="information",
        )
