"""Core module for depswiz."""

from depswiz.core.config import Config, load_config
from depswiz.core.models import (
    AuditResult,
    CheckResult,
    LicenseInfo,
    LicenseResult,
    Package,
    Severity,
    UpdateType,
    Vulnerability,
)

__all__ = [
    "AuditResult",
    "CheckResult",
    "Config",
    "LicenseInfo",
    "LicenseResult",
    "Package",
    "Severity",
    "UpdateType",
    "Vulnerability",
    "load_config",
]
