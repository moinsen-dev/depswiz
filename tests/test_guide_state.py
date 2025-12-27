"""Tests for guide module state management."""

from datetime import datetime

import pytest

from depswiz.guide.state import GuideMode, GuideState, WizardState


class TestGuideMode:
    """Tests for GuideMode enum."""

    def test_mode_values(self) -> None:
        """Test all guide modes exist."""
        assert GuideMode.DASHBOARD
        assert GuideMode.WIZARD
        assert GuideMode.CHAT


class TestWizardState:
    """Tests for WizardState enum."""

    def test_all_states_exist(self) -> None:
        """Test all wizard states are defined."""
        states = [
            WizardState.START,
            WizardState.WELCOME,
            WizardState.PROJECT_SCAN,
            WizardState.SHOW_FINDINGS,
            WizardState.DECISION_TREE,
            WizardState.FIX_VULNERABILITIES,
            WizardState.UPDATE_DEPENDENCIES,
            WizardState.LICENSE_CHECK,
            WizardState.SBOM_GENERATE,
            WizardState.AI_SUGGEST,
            WizardState.CONFIRM_ACTION,
            WizardState.EXECUTE,
            WizardState.REPORT,
            WizardState.NEXT_ACTION,
            WizardState.EXIT,
            WizardState.ERROR,
        ]
        assert len(states) == 16


class TestGuideState:
    """Tests for GuideState dataclass."""

    @pytest.fixture
    def empty_state(self) -> GuideState:
        """Create an empty guide state."""
        return GuideState()

    def test_default_values(self, empty_state: GuideState) -> None:
        """Test default state values."""
        assert empty_state.check_result is None
        assert empty_state.audit_result is None
        assert empty_state.license_result is None
        assert empty_state.tools_result is None
        assert empty_state.is_scanning is False
        assert empty_state.scan_progress == ""
        assert empty_state.last_scan_time is None
        assert empty_state.selected_packages == set()
        assert empty_state.current_mode == GuideMode.DASHBOARD
        assert empty_state.wizard_state == WizardState.START
        assert empty_state.user_preferences == {}
        assert empty_state.actions_taken == []
        assert empty_state.errors == []
        assert empty_state.ai_available is False
        assert empty_state.ai_suggestions is None

    def test_health_score_perfect(self, empty_state: GuideState) -> None:
        """Test health score is 100 with no results."""
        # With no scan results, score is perfect
        assert empty_state.health_score == 100

    def test_health_status(self, empty_state: GuideState) -> None:
        """Test health status for different scores."""
        # Perfect score
        assert empty_state.health_status == "Excellent"

    def test_health_color_green(self, empty_state: GuideState) -> None:
        """Test health color is green for high score."""
        assert empty_state.health_color == "green"

    def test_total_vulnerabilities_empty(self, empty_state: GuideState) -> None:
        """Test vulnerability counts with no results."""
        assert empty_state.total_vulnerabilities == 0
        assert empty_state.critical_count == 0
        assert empty_state.high_count == 0
        assert empty_state.medium_count == 0
        assert empty_state.low_count == 0

    def test_update_breakdown_empty(self, empty_state: GuideState) -> None:
        """Test update breakdown with no results."""
        breakdown = empty_state.update_breakdown
        assert breakdown["major"] == 0
        assert breakdown["minor"] == 0
        assert breakdown["patch"] == 0

    def test_total_packages_empty(self, empty_state: GuideState) -> None:
        """Test total_packages with no results."""
        assert empty_state.total_packages == 0

    def test_outdated_count_empty(self, empty_state: GuideState) -> None:
        """Test outdated_count with no results."""
        assert empty_state.outdated_count == 0

    def test_violation_count_empty(self, empty_state: GuideState) -> None:
        """Test violation_count with no results."""
        assert empty_state.violation_count == 0

    def test_warning_count_empty(self, empty_state: GuideState) -> None:
        """Test warning_count with no results."""
        assert empty_state.warning_count == 0

    def test_license_compliance_pct_empty(self, empty_state: GuideState) -> None:
        """Test license compliance percentage with no results."""
        assert empty_state.license_compliance_pct == 100

    def test_outdated_tools_count_empty(self, empty_state: GuideState) -> None:
        """Test outdated_tools_count with no results."""
        assert empty_state.outdated_tools_count == 0

    def test_tools_count_empty(self, empty_state: GuideState) -> None:
        """Test tools_count with no results."""
        assert empty_state.tools_count == 0

    def test_subscribe_and_notify(self, empty_state: GuideState) -> None:
        """Test observer subscription and notification."""
        notifications = []

        def observer(state: GuideState) -> None:
            notifications.append(state.scan_progress)

        empty_state.subscribe(observer)
        empty_state.scan_progress = "Testing"
        empty_state.notify()
        empty_state.scan_progress = "Progress"
        empty_state.notify()

        assert len(notifications) == 2
        assert notifications[0] == "Testing"
        assert notifications[1] == "Progress"

    def test_unsubscribe(self, empty_state: GuideState) -> None:
        """Test unsubscribe removes observer."""
        notifications = []

        def observer(state: GuideState) -> None:
            notifications.append(1)

        empty_state.subscribe(observer)

        # First notification should work
        empty_state.notify()
        assert len(notifications) == 1

        # Unsubscribe
        empty_state.unsubscribe(observer)

        # Second notification should not reach observer
        empty_state.notify()
        assert len(notifications) == 1

    def test_reset(self, empty_state: GuideState) -> None:
        """Test state reset clears results."""
        empty_state.is_scanning = True
        empty_state.scan_progress = "Testing"
        empty_state.errors.append("Error")
        empty_state.actions_taken.append("Action")
        empty_state.selected_packages.add("test")

        empty_state.reset()

        assert empty_state.check_result is None
        assert empty_state.audit_result is None
        assert empty_state.license_result is None
        assert empty_state.tools_result is None
        assert empty_state.is_scanning is False
        assert empty_state.scan_progress == ""
        assert empty_state.errors == []
        assert empty_state.actions_taken == []
        assert empty_state.selected_packages == set()

    def test_is_scanning_state(self, empty_state: GuideState) -> None:
        """Test scanning state management."""
        assert not empty_state.is_scanning

        empty_state.is_scanning = True
        assert empty_state.is_scanning

        empty_state.is_scanning = False
        assert not empty_state.is_scanning

    def test_last_scan_time(self, empty_state: GuideState) -> None:
        """Test last scan time tracking."""
        assert empty_state.last_scan_time is None

        now = datetime.now()
        empty_state.last_scan_time = now
        assert empty_state.last_scan_time == now

    def test_user_preferences(self, empty_state: GuideState) -> None:
        """Test user preferences storage."""
        empty_state.user_preferences["theme"] = "dark"
        empty_state.user_preferences["auto_fix"] = True

        assert empty_state.user_preferences["theme"] == "dark"
        assert empty_state.user_preferences["auto_fix"] is True

    def test_selected_packages(self, empty_state: GuideState) -> None:
        """Test package selection."""
        empty_state.selected_packages.add("requests")
        empty_state.selected_packages.add("flask")

        assert "requests" in empty_state.selected_packages
        assert "flask" in empty_state.selected_packages
        assert len(empty_state.selected_packages) == 2

    def test_ai_availability(self, empty_state: GuideState) -> None:
        """Test AI availability flag."""
        assert not empty_state.ai_available

        empty_state.ai_available = True
        assert empty_state.ai_available

    def test_ai_suggestions(self, empty_state: GuideState) -> None:
        """Test AI suggestions storage."""
        assert empty_state.ai_suggestions is None

        empty_state.ai_suggestions = "Consider updating requests to fix security issue."
        assert "requests" in empty_state.ai_suggestions

    def test_current_mode(self, empty_state: GuideState) -> None:
        """Test mode switching."""
        assert empty_state.current_mode == GuideMode.DASHBOARD

        empty_state.current_mode = GuideMode.WIZARD
        assert empty_state.current_mode == GuideMode.WIZARD

        empty_state.current_mode = GuideMode.CHAT
        assert empty_state.current_mode == GuideMode.CHAT

    def test_wizard_state(self, empty_state: GuideState) -> None:
        """Test wizard state transitions."""
        assert empty_state.wizard_state == WizardState.START

        empty_state.wizard_state = WizardState.PROJECT_SCAN
        assert empty_state.wizard_state == WizardState.PROJECT_SCAN

    def test_actions_taken(self, empty_state: GuideState) -> None:
        """Test actions taken list."""
        empty_state.actions_taken.append("First action")
        empty_state.actions_taken.append("Second action")

        assert len(empty_state.actions_taken) == 2
        assert "First action" in empty_state.actions_taken

    def test_errors(self, empty_state: GuideState) -> None:
        """Test errors list."""
        empty_state.errors.append("Error 1")
        empty_state.errors.append("Error 2")

        assert len(empty_state.errors) == 2
        assert "Error 1" in empty_state.errors

    def test_observer_error_handling(self, empty_state: GuideState) -> None:
        """Test that observer errors don't break notification chain."""
        calls = []

        def bad_observer(state: GuideState) -> None:
            raise ValueError("Observer error")

        def good_observer(state: GuideState) -> None:
            calls.append(1)

        # Subscribe both
        empty_state.subscribe(bad_observer)
        empty_state.subscribe(good_observer)

        # Notify should not raise
        empty_state.notify()

        # Good observer should still be called
        assert len(calls) == 1
