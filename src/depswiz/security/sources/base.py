"""Base class for vulnerability sources."""

from abc import ABC, abstractmethod

import httpx

from depswiz.core.models import Package, Vulnerability


class VulnerabilitySource(ABC):
    """Abstract base class for vulnerability data sources."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Source identifier (e.g., 'osv', 'ghsa')."""

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable name."""

    @abstractmethod
    async def check_package(
        self, client: httpx.AsyncClient, package: Package
    ) -> list[Vulnerability]:
        """Check a package for vulnerabilities.

        Args:
            client: Async HTTP client
            package: Package to check

        Returns:
            List of vulnerabilities found
        """
