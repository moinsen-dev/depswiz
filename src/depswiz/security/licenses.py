"""License compliance checking."""

from depswiz.core.config import LicensesConfig
from depswiz.core.models import LicenseCategory, Package


class LicenseChecker:
    """Checks packages for license compliance."""

    def __init__(self, config: LicensesConfig):
        self.config = config
        self.allowed = set(config.allowed)
        self.denied = set(config.denied)

    def check_packages(
        self, packages: list[Package]
    ) -> tuple[list[tuple[Package, str]], list[tuple[Package, str]]]:
        """Check packages for license compliance.

        Args:
            packages: List of packages to check

        Returns:
            Tuple of (violations, warnings)
        """
        violations = []
        warnings = []

        for pkg in packages:
            violation, warning = self._check_package(pkg)
            if violation:
                violations.append((pkg, violation))
            if warning:
                warnings.append((pkg, warning))

        return violations, warnings

    def _check_package(self, pkg: Package) -> tuple[str | None, str | None]:
        """Check a single package for license compliance.

        Returns:
            Tuple of (violation_reason, warning_reason)
        """
        if pkg.license_info is None:
            if self.config.fail_on_unknown:
                return "License unknown", None
            return None, "License unknown"

        license_id = pkg.license_info.spdx_id

        if license_id is None:
            if self.config.fail_on_unknown:
                return f"License '{pkg.license_info.name}' is not a recognized SPDX ID", None
            return None, f"License '{pkg.license_info.name}' is not a recognized SPDX ID"

        # Check policy mode
        if self.config.policy_mode == "allow":
            # Allowlist mode: license must be in allowed list
            if license_id not in self.allowed:
                return f"License '{license_id}' is not in the allowed list", None
        else:
            # Denylist mode: license must not be in denied list
            if license_id in self.denied:
                return f"License '{license_id}' is in the denied list", None

        # Check for copyleft warning
        if self.config.warn_copyleft and pkg.license_info.is_copyleft:
            category = pkg.license_info.category
            if category == LicenseCategory.STRONG_COPYLEFT:
                return None, f"License '{license_id}' is strong copyleft"
            elif category == LicenseCategory.WEAK_COPYLEFT:
                return None, f"License '{license_id}' is weak copyleft"

        return None, None

    def is_allowed(self, license_id: str) -> bool:
        """Check if a license is allowed by the policy."""
        if self.config.policy_mode == "allow":
            return license_id in self.allowed
        else:
            return license_id not in self.denied
