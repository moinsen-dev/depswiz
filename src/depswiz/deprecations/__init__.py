"""Deprecation detection and fixing for Flutter/Dart projects."""

from depswiz.deprecations.models import (
    Deprecation,
    DeprecationResult,
    DeprecationStatus,
)
from depswiz.deprecations.scanner import scan_deprecations

__all__ = [
    "Deprecation",
    "DeprecationResult",
    "DeprecationStatus",
    "scan_deprecations",
]
