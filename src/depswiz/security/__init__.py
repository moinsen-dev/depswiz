"""Security module for depswiz."""

from depswiz.security.licenses import LicenseChecker
from depswiz.security.vulnerabilities import VulnerabilityAggregator

__all__ = ["LicenseChecker", "VulnerabilityAggregator"]
