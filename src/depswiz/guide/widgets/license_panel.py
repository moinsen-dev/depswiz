"""License panel widget for the guide dashboard."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.panel import Panel
from rich.text import Text
from textual.reactive import reactive
from textual.widget import Widget

if TYPE_CHECKING:
    from depswiz.core.models import LicenseResult


class LicensePanel(Widget):
    """Panel showing license compliance status."""

    compliance_pct: reactive[int] = reactive(100)
    violation_count: reactive[int] = reactive(0)
    warning_count: reactive[int] = reactive(0)
    is_loading: reactive[bool] = reactive(False)

    def render(self) -> Panel:
        """Render the license panel."""
        if self.is_loading:
            return Panel("[italic]Scanning...[/italic]", title="Licenses")

        # Determine color based on compliance
        if self.compliance_pct >= 100:
            color = "green"
        elif self.compliance_pct >= 90:
            color = "yellow"
        else:
            color = "red"

        content = Text()
        content.append(f"{self.compliance_pct}%", style=f"bold {color}")
        content.append(" Compliant\n")

        if self.violation_count > 0:
            content.append(f"{self.violation_count} ", style="red bold")
            content.append("Violations\n", style="red")

        if self.warning_count > 0:
            content.append(f"{self.warning_count} ", style="yellow")
            content.append("Warnings", style="yellow")

        if self.violation_count == 0 and self.warning_count == 0:
            content.append("No issues", style="green dim")

        border_style = (
            "red"
            if self.violation_count > 0
            else ("yellow" if self.warning_count > 0 else "green")
        )

        return Panel(
            content,
            title="Licenses",
            border_style=border_style,
        )

    def update_from_result(self, result: LicenseResult | None, total_packages: int = 0) -> None:
        """Update from a LicenseResult."""
        if result:
            self.violation_count = len(result.violations)
            self.warning_count = len(result.warnings)

            if total_packages > 0:
                issues = self.violation_count + self.warning_count
                self.compliance_pct = max(0, int(100 * (total_packages - issues) / total_packages))
            else:
                self.compliance_pct = 100
        else:
            self.violation_count = 0
            self.warning_count = 0
            self.compliance_pct = 100
