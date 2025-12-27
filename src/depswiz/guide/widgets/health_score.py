"""Health score widget for the guide dashboard."""

from rich.align import Align
from rich.panel import Panel
from rich.text import Text
from textual.reactive import reactive
from textual.widget import Widget


class HealthScoreWidget(Widget):
    """Displays a circular-style health score 0-100."""

    score: reactive[int] = reactive(0)
    status: reactive[str] = reactive("Unknown")

    def render(self) -> Panel:
        """Render the health score panel."""
        # Determine color based on score
        if self.score >= 90 or self.score >= 80:
            color = "green"
        elif self.score >= 60:
            color = "yellow"
        elif self.score >= 40:
            color = "orange1"
        else:
            color = "red"

        score_text = Text()
        score_text.append(f"{self.score}", style=f"bold {color}")
        score_text.append("\n/100\n", style="dim")
        score_text.append(self.status, style=color)

        return Panel(
            Align.center(score_text, vertical="middle"),
            title="Health Score",
            border_style=color,
        )

    def watch_score(self, new_score: int) -> None:
        """React to score changes."""
        self.refresh()

    def watch_status(self, new_status: str) -> None:
        """React to status changes."""
        self.refresh()
