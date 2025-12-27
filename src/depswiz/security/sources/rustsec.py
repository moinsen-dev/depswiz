"""RustSec Advisory Database source for Rust packages.

RustSec maintains a database of security advisories for Rust packages.
This source fetches advisories from the GitHub-hosted database.
"""

from datetime import datetime

import httpx

from depswiz.core.logging import get_logger
from depswiz.core.models import Package, Severity, Vulnerability
from depswiz.security.sources.base import VulnerabilitySource

logger = get_logger("security.rustsec")


class RustSecSource(VulnerabilitySource):
    """RustSec Advisory Database vulnerability source.

    Queries the RustSec database for Rust package vulnerabilities.
    The database is maintained at https://github.com/rustsec/advisory-db
    """

    # Raw GitHub content URL for RustSec advisory database index
    INDEX_URL = (
        "https://raw.githubusercontent.com/rustsec/advisory-db/main/crates/{crate}/{advisory}.toml"
    )
    CRATES_URL = "https://raw.githubusercontent.com/rustsec/advisory-db/main/crates/{crate}"

    # Alternative: Use the crates.io API which includes RustSec data
    CRATES_IO_URL = "https://crates.io/api/v1/crates/{crate}/reverse_dependencies"

    @property
    def name(self) -> str:
        return "rustsec"

    @property
    def display_name(self) -> str:
        return "RustSec Advisory Database"

    async def check_package(
        self, client: httpx.AsyncClient, package: Package
    ) -> list[Vulnerability]:
        """Query RustSec for vulnerabilities affecting a Rust package.

        We use the crates.io API which includes vulnerability data from RustSec.
        """
        if not package.current_version or package.language != "rust":
            return []

        try:
            # Use crates.io API which has RustSec data embedded
            url = f"https://crates.io/api/v1/crates/{package.name}"
            headers = {"User-Agent": "depswiz/1.0.0"}

            response = await client.get(url, headers=headers, timeout=30.0)

            if response.status_code != 200:
                return []

            # Validate response is valid JSON
            response.json()

            # Query GitHub API for RustSec advisories
            return await self._check_rustsec_github(client, package)

        except httpx.HTTPStatusError as e:
            logger.debug("HTTP error querying RustSec for %s: %s", package.name, e)
        except httpx.RequestError as e:
            logger.debug("Request error querying RustSec for %s: %s", package.name, e)
        except Exception as e:
            logger.debug("Unexpected error querying RustSec for %s: %s", package.name, e)

        return []

    async def _check_rustsec_github(
        self, client: httpx.AsyncClient, package: Package
    ) -> list[Vulnerability]:
        """Check RustSec advisory database on GitHub.

        The RustSec database structure is:
        crates/{crate_name}/{RUSTSEC-YYYY-NNNN}.toml
        """
        vulns = []

        try:
            # List advisories for this crate using GitHub API
            url = f"https://api.github.com/repos/rustsec/advisory-db/contents/crates/{package.name}"
            headers = {
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "depswiz/1.0.0",
            }

            response = await client.get(url, headers=headers, timeout=15.0)

            if response.status_code == 404:
                # No advisories for this crate
                return []

            if response.status_code != 200:
                return []

            files = response.json()

            # Fetch each advisory file
            current_version = package.current_version
            for file_info in files:
                if file_info.get("name", "").endswith(".toml"):
                    advisory_url = file_info.get("download_url")
                    if advisory_url and current_version:
                        vuln = await self._fetch_advisory(
                            client, advisory_url, current_version
                        )
                        if vuln:
                            vulns.append(vuln)

        except httpx.HTTPStatusError as e:
            logger.debug("HTTP error checking RustSec GitHub for %s: %s", package.name, e)
        except httpx.RequestError as e:
            logger.debug("Request error checking RustSec GitHub for %s: %s", package.name, e)
        except Exception as e:
            logger.debug("Unexpected error checking RustSec GitHub for %s: %s", package.name, e)

        return vulns

    async def _fetch_advisory(
        self, client: httpx.AsyncClient, url: str, current_version: str
    ) -> Vulnerability | None:
        """Fetch and parse a single RustSec advisory TOML file."""
        try:
            import tomllib

            response = await client.get(url, timeout=10.0)

            if response.status_code != 200:
                return None

            # Parse TOML advisory
            data = tomllib.loads(response.text)
            advisory = data.get("advisory", {})

            vuln_id = advisory.get("id", "")
            if not vuln_id:
                return None

            # Check version requirements
            versions = data.get("versions", {})
            patched = versions.get("patched", [])
            unaffected = versions.get("unaffected", [])

            # Determine if current version is vulnerable
            if not self._is_version_vulnerable(current_version, patched, unaffected):
                return None

            # Map keywords to severity
            severity = Severity.UNKNOWN
            keywords = advisory.get("keywords", [])
            if "code-execution" in keywords or "memory-corruption" in keywords:
                severity = Severity.CRITICAL
            elif (
                "denial-of-service" in keywords
                or "memory-exposure" in keywords
                or "crypto-failure" in keywords
            ):
                severity = Severity.HIGH
            elif keywords:
                severity = Severity.MEDIUM

            # Get CVE aliases
            aliases = advisory.get("aliases", [])

            # Get references
            references = advisory.get("references", [])
            if advisory.get("url"):
                references.insert(0, advisory["url"])

            # Parse date
            published = None
            date_str = advisory.get("date")
            if date_str:
                try:
                    published = datetime.strptime(date_str, "%Y-%m-%d")
                except Exception:
                    pass

            # Build affected versions string
            affected_str = ""
            if patched:
                affected_str = (
                    f"< {patched[0]}" if len(patched) == 1 else f"patched in: {', '.join(patched)}"
                )

            return Vulnerability(
                id=vuln_id,
                aliases=aliases,
                severity=severity,
                cvss_score=None,
                cvss_vector=None,
                title=advisory.get("title", vuln_id),
                description=advisory.get("description", ""),
                affected_versions=affected_str,
                fixed_version=patched[0] if patched else None,
                source=self.name,
                references=references[:5],
                published=published,
                modified=None,
                cwe_ids=[],
            )

        except Exception as e:
            logger.debug("Error parsing RustSec advisory from %s: %s", url, e)
            return None

    def _is_version_vulnerable(
        self, current: str, patched: list[str], unaffected: list[str]
    ) -> bool:
        """Check if current version is vulnerable based on patched/unaffected lists.

        RustSec uses semver requirements like ">= 1.0.0" for patched versions.
        """
        try:
            from packaging.version import Version

            current_ver = Version(current)

            # Check if in unaffected versions
            for requirement in unaffected:
                if self._version_matches_requirement(current_ver, requirement):
                    return False

            # Check if in patched versions
            for requirement in patched:
                if self._version_matches_requirement(current_ver, requirement):
                    return False

            # If no explicit exemptions, assume vulnerable
            return True

        except Exception:
            # Conservative: assume vulnerable if we can't parse
            return True

    def _version_matches_requirement(self, version, requirement: str) -> bool:
        """Check if version matches a semver requirement string."""
        try:
            from packaging.version import Version

            requirement = requirement.strip()

            if requirement.startswith(">="):
                return version >= Version(requirement[2:].strip())
            elif requirement.startswith(">"):
                return version > Version(requirement[1:].strip())
            elif requirement.startswith("<="):
                return version <= Version(requirement[2:].strip())
            elif requirement.startswith("<"):
                return version < Version(requirement[1:].strip())
            elif requirement.startswith("^"):
                # Caret requirement: ^1.2.3 means >=1.2.3, <2.0.0
                base = Version(requirement[1:].strip())
                return version >= base and version.major == base.major
            elif requirement.startswith("~"):
                # Tilde requirement: ~1.2.3 means >=1.2.3, <1.3.0
                base = Version(requirement[1:].strip())
                return (
                    version >= base and version.major == base.major and version.minor == base.minor
                )
            else:
                # Exact match
                return version == Version(requirement)

        except Exception:
            return False
