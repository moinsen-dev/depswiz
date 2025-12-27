"""Custom Textual widgets for the guide dashboard."""

from depswiz.guide.widgets.health_score import HealthScoreWidget
from depswiz.guide.widgets.license_panel import LicensePanel
from depswiz.guide.widgets.tools_panel import ToolsPanel
from depswiz.guide.widgets.updates_panel import UpdatesPanel
from depswiz.guide.widgets.vulnerability_panel import VulnerabilityPanel

__all__ = [
    "HealthScoreWidget",
    "LicensePanel",
    "ToolsPanel",
    "UpdatesPanel",
    "VulnerabilityPanel",
]
