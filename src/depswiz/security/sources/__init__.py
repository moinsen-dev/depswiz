"""Vulnerability sources for depswiz."""

from depswiz.security.sources.base import VulnerabilitySource
from depswiz.security.sources.ghsa import GhsaSource
from depswiz.security.sources.nvd import NvdSource
from depswiz.security.sources.osv import OsvSource
from depswiz.security.sources.rustsec import RustSecSource

__all__ = ["GhsaSource", "NvdSource", "OsvSource", "RustSecSource", "VulnerabilitySource"]
