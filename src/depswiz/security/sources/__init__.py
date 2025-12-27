"""Vulnerability sources for depswiz."""

from depswiz.security.sources.base import VulnerabilitySource
from depswiz.security.sources.osv import OsvSource

__all__ = ["OsvSource", "VulnerabilitySource"]
