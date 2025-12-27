"""Security module for depswiz."""

from depswiz.security.vulnerabilities import VulnerabilityAggregator
from depswiz.security.licenses import LicenseChecker

__all__ = ["VulnerabilityAggregator", "LicenseChecker"]
