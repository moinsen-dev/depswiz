"""Base output formatter for depswiz."""

from abc import ABC, abstractmethod

from depswiz.core.models import AuditResult, CheckResult, LicenseResult


class OutputFormatter(ABC):
    """Abstract base class for output formatters."""

    @abstractmethod
    def format_check_result(self, result: CheckResult, warn_breaking: bool = True) -> str:
        """Format a check result."""

    @abstractmethod
    def format_audit_result(self, result: AuditResult, show_fix: bool = False) -> str:
        """Format an audit result."""

    @abstractmethod
    def format_license_result(self, result: LicenseResult, summary_only: bool = False) -> str:
        """Format a license result."""
