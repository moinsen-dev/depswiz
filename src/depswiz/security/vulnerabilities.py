"""Vulnerability aggregation and checking."""

import asyncio
from typing import Optional

import httpx

from depswiz.core.config import Config
from depswiz.core.models import Package, Vulnerability
from depswiz.security.sources.osv import OsvSource


class VulnerabilityAggregator:
    """Aggregates vulnerability data from multiple sources."""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.sources = []

        # Initialize enabled sources
        enabled_sources = self.config.audit.sources if config else ["osv"]

        if "osv" in enabled_sources:
            self.sources.append(OsvSource())

        # TODO: Add more sources
        # if "ghsa" in enabled_sources:
        #     self.sources.append(GhsaSource())
        # if "rustsec" in enabled_sources:
        #     self.sources.append(RustSecSource())

    async def check_packages(
        self, packages: list[Package]
    ) -> list[tuple[Package, Vulnerability]]:
        """Check multiple packages for vulnerabilities.

        Args:
            packages: List of packages to check

        Returns:
            List of (package, vulnerability) tuples
        """
        all_vulnerabilities: list[tuple[Package, Vulnerability]] = []

        async with httpx.AsyncClient(timeout=self.config.network.timeout_seconds) as client:
            semaphore = asyncio.Semaphore(self.config.network.max_concurrent_requests)

            async def check_one(pkg: Package) -> list[tuple[Package, Vulnerability]]:
                async with semaphore:
                    vulns = await self._check_package(client, pkg)
                    return [(pkg, v) for v in vulns]

            tasks = [check_one(pkg) for pkg in packages]
            results = await asyncio.gather(*tasks)

            for pkg_vulns in results:
                all_vulnerabilities.extend(pkg_vulns)

        # Deduplicate vulnerabilities (same vuln might come from multiple sources)
        seen = set()
        deduplicated = []
        for pkg, vuln in all_vulnerabilities:
            key = (pkg.name, pkg.current_version, vuln.id)
            if key not in seen:
                seen.add(key)
                deduplicated.append((pkg, vuln))

        # Sort by severity (critical first)
        deduplicated.sort(key=lambda x: x[1].severity, reverse=True)

        return deduplicated

    async def _check_package(
        self, client: httpx.AsyncClient, package: Package
    ) -> list[Vulnerability]:
        """Check a single package against all sources."""
        all_vulns = []

        for source in self.sources:
            try:
                vulns = await source.check_package(client, package)
                all_vulns.extend(vulns)
            except Exception:
                # Log but continue with other sources
                pass

        return all_vulns

    async def check_package(self, package: Package) -> list[Vulnerability]:
        """Check a single package for vulnerabilities."""
        async with httpx.AsyncClient(timeout=self.config.network.timeout_seconds) as client:
            return await self._check_package(client, package)
