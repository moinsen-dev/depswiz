"""Centralized state management for the guide module."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from depswiz.core.models import (
        AuditResult,
        CheckResult,
        LicenseResult,
    )
    from depswiz.tools.models import ToolsCheckResult


class GuideMode(Enum):
    """Available guide interaction modes."""

    DASHBOARD = auto()  # Full TUI with Textual
    WIZARD = auto()  # Step-by-step InquirerPy prompts
    CHAT = auto()  # Conversational Claude interface


class WizardState(Enum):
    """Wizard state machine states."""

    START = auto()
    WELCOME = auto()
    PROJECT_SCAN = auto()
    SHOW_FINDINGS = auto()
    DECISION_TREE = auto()
    FIX_VULNERABILITIES = auto()
    UPDATE_DEPENDENCIES = auto()
    LICENSE_CHECK = auto()
    SBOM_GENERATE = auto()
    AI_SUGGEST = auto()
    CONFIRM_ACTION = auto()
    EXECUTE = auto()
    REPORT = auto()
    NEXT_ACTION = auto()
    EXIT = auto()
    ERROR = auto()


@dataclass
class GuideState:
    """Centralized state for the guide application.

    This class holds all scan results, UI state, and computed properties
    needed by the TUI dashboard, wizard, and chat modes.
    """

    # Scan results (populated by workers)
    check_result: CheckResult | None = None
    audit_result: AuditResult | None = None
    license_result: LicenseResult | None = None
    tools_result: ToolsCheckResult | None = None

    # Scan state
    is_scanning: bool = False
    scan_progress: str = ""
    last_scan_time: datetime | None = None

    # UI state
    selected_packages: set[str] = field(default_factory=set)
    current_mode: GuideMode = GuideMode.DASHBOARD
    wizard_state: WizardState = WizardState.START

    # User preferences from wizard
    user_preferences: dict[str, Any] = field(default_factory=dict)

    # Actions taken during session
    actions_taken: list[str] = field(default_factory=list)

    # Errors encountered
    errors: list[str] = field(default_factory=list)

    # AI availability
    ai_available: bool = False
    ai_suggestions: str | None = None

    # Observers for reactive updates
    _observers: list[Callable[[GuideState], None]] = field(default_factory=list)

    @property
    def health_score(self) -> int:
        """Calculate overall project health score (0-100).

        Scoring algorithm:
        - Start with 100 points
        - Deduct for vulnerabilities (weighted by severity)
        - Deduct for outdated packages (weighted by update type)
        - Deduct for license violations

        Returns:
            Integer score from 0 (critical) to 100 (perfect)
        """
        score = 100

        # Deduct for vulnerabilities (major impact)
        if self.audit_result:
            score -= self.critical_count * 25  # Critical = -25 each
            score -= self.high_count * 15  # High = -15 each
            score -= self.medium_count * 5  # Medium = -5 each
            score -= self.low_count * 1  # Low = -1 each

        # Deduct for outdated packages (moderate impact)
        if self.check_result:
            breakdown = self.update_breakdown
            score -= breakdown.get("major", 0) * 3  # Major = -3 each
            score -= breakdown.get("minor", 0) * 1  # Minor = -1 each
            # Patch updates don't affect health score

        # Deduct for license violations (moderate impact)
        if self.license_result:
            score -= self.violation_count * 10  # Violation = -10 each
            score -= self.warning_count * 2  # Warning = -2 each

        return max(0, min(100, score))

    @property
    def health_status(self) -> str:
        """Get human-readable health status."""
        score = self.health_score
        if score >= 90:
            return "Excellent"
        elif score >= 80:
            return "Good"
        elif score >= 60:
            return "Fair"
        elif score >= 40:
            return "Poor"
        else:
            return "Critical"

    @property
    def health_color(self) -> str:
        """Get color for health score display."""
        score = self.health_score
        if score >= 80:
            return "green"
        elif score >= 60:
            return "yellow"
        elif score >= 40:
            return "orange1"
        else:
            return "red"

    # Vulnerability counts
    @property
    def total_vulnerabilities(self) -> int:
        """Total number of vulnerabilities."""
        if not self.audit_result:
            return 0
        return len(self.audit_result.vulnerabilities)

    @property
    def critical_count(self) -> int:
        """Number of critical severity vulnerabilities."""
        if not self.audit_result:
            return 0
        return self.audit_result.critical_count

    @property
    def high_count(self) -> int:
        """Number of high severity vulnerabilities."""
        if not self.audit_result:
            return 0
        return self.audit_result.high_count

    @property
    def medium_count(self) -> int:
        """Number of medium severity vulnerabilities."""
        if not self.audit_result:
            return 0
        return self.audit_result.medium_count

    @property
    def low_count(self) -> int:
        """Number of low severity vulnerabilities."""
        if not self.audit_result:
            return 0
        return self.audit_result.low_count

    # Update counts
    @property
    def total_packages(self) -> int:
        """Total number of packages."""
        if not self.check_result:
            return 0
        return self.check_result.total_packages

    @property
    def outdated_count(self) -> int:
        """Number of outdated packages."""
        if not self.check_result:
            return 0
        return len(self.check_result.outdated_packages)

    @property
    def update_breakdown(self) -> dict[str, int]:
        """Get counts of updates by type (major/minor/patch)."""
        if not self.check_result:
            return {"major": 0, "minor": 0, "patch": 0}

        from depswiz.core.models import UpdateType

        breakdown = {"major": 0, "minor": 0, "patch": 0}
        for pkg in self.check_result.outdated_packages:
            if pkg.update_type == UpdateType.MAJOR:
                breakdown["major"] += 1
            elif pkg.update_type == UpdateType.MINOR:
                breakdown["minor"] += 1
            elif pkg.update_type == UpdateType.PATCH:
                breakdown["patch"] += 1
        return breakdown

    # License counts
    @property
    def violation_count(self) -> int:
        """Number of license violations."""
        if not self.license_result:
            return 0
        return len(self.license_result.violations)

    @property
    def warning_count(self) -> int:
        """Number of license warnings."""
        if not self.license_result:
            return 0
        return len(self.license_result.warnings)

    @property
    def license_compliance_pct(self) -> int:
        """License compliance percentage."""
        if not self.license_result or not self.check_result:
            return 100
        total = self.check_result.total_packages
        if total == 0:
            return 100
        violations = self.violation_count + self.warning_count
        return max(0, int(100 * (total - violations) / total))

    # Tools status
    @property
    def outdated_tools_count(self) -> int:
        """Number of development tools that need updating."""
        if not self.tools_result:
            return 0
        return sum(1 for tool in self.tools_result.tools if tool.has_update)

    @property
    def tools_count(self) -> int:
        """Total number of detected development tools."""
        if not self.tools_result:
            return 0
        return len(self.tools_result.tools)

    # Observer pattern for reactive updates
    def subscribe(self, callback: Callable[[GuideState], None]) -> None:
        """Subscribe to state changes.

        Args:
            callback: Function to call when state changes
        """
        self._observers.append(callback)

    def unsubscribe(self, callback: Callable[[GuideState], None]) -> None:
        """Unsubscribe from state changes.

        Args:
            callback: Function to remove from observers
        """
        if callback in self._observers:
            self._observers.remove(callback)

    def notify(self) -> None:
        """Notify all observers of state change."""
        for callback in self._observers:
            try:
                callback(self)
            except Exception:
                pass  # Don't let observer errors break the notification chain

    def reset(self) -> None:
        """Reset state to initial values."""
        self.check_result = None
        self.audit_result = None
        self.license_result = None
        self.tools_result = None
        self.is_scanning = False
        self.scan_progress = ""
        self.last_scan_time = None
        self.selected_packages = set()
        self.wizard_state = WizardState.START
        self.user_preferences = {}
        self.actions_taken = []
        self.errors = []
        self.ai_suggestions = None
        self.notify()
