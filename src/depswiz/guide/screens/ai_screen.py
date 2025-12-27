"""AI suggestions screen showing Claude-powered analysis."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import ScrollableContainer
from textual.screen import ModalScreen
from textual.widgets import Footer, Static

if TYPE_CHECKING:
    from depswiz.guide.context import ContextManager
    from depswiz.guide.state import GuideState


class AIScreen(ModalScreen):
    """Modal screen showing AI-powered analysis and suggestions."""

    BINDINGS = [
        Binding("escape", "dismiss", "Close"),
        Binding("q", "dismiss", "Close"),
        Binding("r", "refresh_analysis", "Refresh"),
    ]

    CSS = """
    AIScreen {
        align: center middle;
    }

    #ai-container {
        width: 90%;
        height: 90%;
        background: $surface;
        border: solid $primary;
        padding: 1;
    }

    #ai-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    #ai-content {
        height: 100%;
        overflow-y: auto;
    }

    #ai-loading {
        text-align: center;
        text-style: italic;
        color: $text-muted;
    }
    """

    def __init__(
        self,
        state: GuideState,
        context_manager: ContextManager,
    ) -> None:
        """Initialize the AI screen.

        Args:
            state: Guide state
            context_manager: Project context manager
        """
        super().__init__()
        self.state = state
        self.context_manager = context_manager
        self.analysis_result: str | None = None

    def compose(self) -> ComposeResult:
        """Compose the AI screen layout."""
        with ScrollableContainer(id="ai-container"):
            yield Static(self._render_title(), id="ai-title")
            yield Static(self._render_initial_content(), id="ai-content")
        yield Footer()

    def _render_title(self) -> Text:
        """Render the screen title."""
        title = Text()
        title.append("AI-Powered Analysis", style="bold magenta")
        return title

    def _render_initial_content(self) -> Panel:
        """Render initial content while loading."""
        return Panel(
            Text("Analyzing your project...", style="italic"),
            title="Loading",
            border_style="blue",
        )

    async def on_mount(self) -> None:
        """Start analysis when screen mounts."""
        await self._run_analysis()

    async def _run_analysis(self) -> None:
        """Run the AI analysis."""
        content_widget = self.query_one("#ai-content", Static)

        try:
            # Check if Claude is available
            from depswiz.ai.claude_client import is_available, run_claude

            if not is_available():
                content_widget.update(self._render_fallback_analysis())
                return

            # Build context for Claude
            prompt = self._build_prompt()

            # Show loading state
            content_widget.update(
                Panel(
                    Text("Consulting Claude for analysis...", style="italic blue"),
                    title="Working",
                    border_style="blue",
                )
            )

            # Run Claude analysis
            try:
                response = run_claude(
                    prompt,
                    timeout=120,
                    cwd=self.context_manager.project_path,
                )
                self.analysis_result = response
                content_widget.update(self._render_ai_response(response))
            except Exception as e:
                content_widget.update(
                    Panel(
                        f"Claude analysis failed: {e}\n\nFalling back to rule-based analysis.",
                        title="Error",
                        border_style="red",
                    )
                )
                # Show fallback after brief delay
                content_widget.update(self._render_fallback_analysis())

        except ImportError:
            content_widget.update(self._render_fallback_analysis())

    def _build_prompt(self) -> str:
        """Build the analysis prompt for Claude."""
        ctx = self.context_manager.project_context

        prompt_parts = ["Analyze this project's dependency health and provide recommendations:"]

        if ctx:
            prompt_parts.append(f"\nProject: {ctx.path.name}")
            prompt_parts.append(f"Languages: {', '.join(ctx.languages)}")

        if self.state.check_result:
            prompt_parts.append(f"\nTotal packages: {self.state.total_packages}")
            prompt_parts.append(f"Outdated: {self.state.outdated_count}")

        if self.state.audit_result:
            prompt_parts.append(f"\nVulnerabilities: {self.state.total_vulnerabilities}")
            prompt_parts.append(f"  Critical: {self.state.critical_count}")
            prompt_parts.append(f"  High: {self.state.high_count}")

        if self.state.license_result:
            prompt_parts.append(f"\nLicense violations: {self.state.violation_count}")
            prompt_parts.append(f"License warnings: {self.state.warning_count}")

        prompt_parts.append(f"\nHealth score: {self.state.health_score}/100")

        prompt_parts.append("""

Please provide:
1. A brief assessment of the project's dependency health
2. Top 3 priority actions to improve security and maintainability
3. Any specific packages that need immediate attention
4. Suggestions for long-term maintenance

Keep the response concise and actionable.""")

        return "\n".join(prompt_parts)

    def _render_ai_response(self, response: str) -> Panel:
        """Render Claude's response."""
        return Panel(
            Markdown(response),
            title="Claude's Analysis",
            border_style="green",
        )

    def _render_fallback_analysis(self) -> Panel:
        """Render fallback analysis when Claude is not available."""
        lines = ["## Dependency Health Analysis\n"]

        # Health assessment
        score = self.state.health_score
        if score >= 90:
            lines.append("**Overall Health:** Excellent - Your project is in great shape!\n")
        elif score >= 80:
            lines.append("**Overall Health:** Good - Minor improvements possible.\n")
        elif score >= 60:
            lines.append("**Overall Health:** Fair - Some issues need attention.\n")
        else:
            lines.append("**Overall Health:** Poor - Immediate action recommended.\n")

        # Priority actions
        lines.append("### Priority Actions\n")

        priorities = []
        if self.state.critical_count > 0:
            priorities.append(
                f"1. **CRITICAL:** Fix {self.state.critical_count} critical vulnerabilities"
            )
        if self.state.high_count > 0:
            priorities.append(f"2. Address {self.state.high_count} high severity vulnerabilities")
        if self.state.violation_count > 0:
            priorities.append(f"3. Review {self.state.violation_count} license violations")

        breakdown = self.state.update_breakdown
        if breakdown.get("major", 0) > 0:
            priorities.append(f"4. Consider {breakdown['major']} major version updates")

        if priorities:
            lines.extend(priorities)
        else:
            lines.append("No urgent actions needed!")

        # Summary stats
        lines.append("\n### Summary")
        lines.append(f"- Health Score: {self.state.health_score}/100")
        lines.append(f"- Total Packages: {self.state.total_packages}")
        lines.append(f"- Outdated: {self.state.outdated_count}")
        lines.append(f"- Vulnerabilities: {self.state.total_vulnerabilities}")
        lines.append(f"- License Issues: {self.state.violation_count + self.state.warning_count}")

        lines.append("\n*For AI-powered analysis, install Claude Code CLI.*")

        return Panel(
            Markdown("\n".join(lines)),
            title="Analysis (Fallback Mode)",
            border_style="yellow",
        )

    def action_dismiss(self) -> None:
        """Close the screen."""
        self.app.pop_screen()

    def action_refresh_analysis(self) -> None:
        """Refresh the analysis."""
        self.run_worker(self._run_analysis())
