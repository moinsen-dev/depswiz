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

    def format_comprehensive_scan(
        self,
        check_result: CheckResult,
        audit_result: AuditResult,
        license_result: LicenseResult,
    ) -> str:
        """Format a comprehensive scan result combining all checks.

        Default implementation combines individual format methods.
        Subclasses can override for better integration.
        """
        parts = [
            self.format_check_result(check_result),
            self.format_audit_result(audit_result),
            self.format_license_result(license_result),
        ]
        return "\n".join(filter(None, parts))
