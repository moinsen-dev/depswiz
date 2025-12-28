"""NVD (National Vulnerability Database) data source.

The NVD is maintained by NIST and provides comprehensive CVE data
with CVSS scoring. It's considered the "gold standard" for vulnerability data.

API Reference: https://nvd.nist.gov/developers/vulnerabilities
"""

import os
from datetime import datetime
from urllib.parse import quote

import httpx

from depswiz.core.logging import get_logger
from depswiz.core.models import Package, Severity, Vulnerability
from depswiz.security.sources.base import VulnerabilitySource

logger = get_logger("security.nvd")

# Mapping from plugin names to CPE vendor/product patterns
# CPE format: cpe:2.3:a:vendor:product:version:*:*:*:*:*:*:*
CPE_PATTERNS = {
    "python": [
        # Search by package name as keyword
        ("pypi", "{package}"),
    ],
    "javascript": [
        ("npm", "{package}"),
        ("nodejs", "{package}"),
    ],
    "rust": [
        ("rust-lang", "{package}"),
        ("crates.io", "{package}"),
    ],
    "golang": [
        ("golang", "{package}"),
        ("go", "{package}"),
    ],
    "dart": [
        ("dart", "{package}"),
        ("pub.dev", "{package}"),
    ],
}


class NvdSource(VulnerabilitySource):
    """NVD (National Vulnerability Database) vulnerability source.

    Uses the NVD 2.0 API to query CVEs. An API key is recommended for
    higher rate limits (set NVD_API_KEY environment variable).

    Without API key: 5 requests per 30 seconds
    With API key: 50 requests per 30 seconds
    """

    NVD_API = "https://services.nvd.nist.gov/rest/json/cves/2.0"

    @property
    def name(self) -> str:
        return "nvd"

    @property
    def display_name(self) -> str:
        return "National Vulnerability Database (NVD)"

    def _get_api_key(self) -> str | None:
        """Get NVD API key from environment."""
        return os.environ.get("NVD_API_KEY")

    async def check_package(
        self, client: httpx.AsyncClient, package: Package
    ) -> list[Vulnerability]:
        """Query NVD for vulnerabilities affecting a package.

        NVD doesn't have direct package name lookups like OSV or GHSA,
        so we search by keyword and CPE patterns.
        """
        if not package.current_version or not package.language:
            return []

        patterns = CPE_PATTERNS.get(package.language)
        if not patterns:
            return []

        vulns = []
        seen_cve_ids: set[str] = set()

        # Try keyword search with package name
        try:
            keyword_vulns = await self._search_by_keyword(client, package)
            for vuln in keyword_vulns:
                if vuln.id not in seen_cve_ids:
                    seen_cve_ids.add(vuln.id)
                    vulns.append(vuln)
        except Exception as e:
            logger.debug("Error searching NVD by keyword for %s: %s", package.name, e)

        return vulns

    async def _search_by_keyword(
        self, client: httpx.AsyncClient, package: Package
    ) -> list[Vulnerability]:
        """Search NVD by package name as keyword."""
        vulns = []

        try:
            # Build query params
            params = {
                "keywordSearch": package.name,
                "resultsPerPage": "20",
            }

            headers = {
                "User-Agent": "depswiz/1.0.0",
            }

            # Add API key if available
            api_key = self._get_api_key()
            if api_key:
                headers["apiKey"] = api_key

            response = await client.get(
                self.NVD_API,
                params=params,
                headers=headers,
                timeout=60.0,  # NVD can be slow
            )

            if response.status_code == 403:
                logger.debug("NVD rate limit exceeded, skipping %s", package.name)
                return []

            if response.status_code != 200:
                logger.debug("NVD returned status %d for %s", response.status_code, package.name)
                return []

            data = response.json()
            vulnerabilities = data.get("vulnerabilities", [])

            for vuln_data in vulnerabilities:
                vuln = self._parse_vulnerability(vuln_data, package)
                if vuln:
                    vulns.append(vuln)

        except httpx.HTTPStatusError as e:
            logger.debug("HTTP error querying NVD for %s: %s", package.name, e)
        except httpx.RequestError as e:
            logger.debug("Request error querying NVD for %s: %s", package.name, e)
        except Exception as e:
            logger.debug("Unexpected error querying NVD for %s: %s", package.name, e)

        return vulns

    def _parse_vulnerability(self, data: dict, package: Package) -> Vulnerability | None:
        """Parse NVD vulnerability data into our model."""
        try:
            cve_data = data.get("cve", {})
            cve_id = cve_data.get("id", "")

            if not cve_id:
                return None

            # Check if this CVE is actually related to our package
            # by checking the affected configurations
            if not self._is_package_affected(cve_data, package):
                return None

            # Get descriptions (prefer English)
            descriptions = cve_data.get("descriptions", [])
            description = ""
            for desc in descriptions:
                if desc.get("lang") == "en":
                    description = desc.get("value", "")
                    break
            if not description and descriptions:
                description = descriptions[0].get("value", "")

            # Extract CVSS metrics
            severity = Severity.UNKNOWN
            cvss_score = None
            cvss_vector = None

            metrics = cve_data.get("metrics", {})

            # Try CVSS 3.1 first
            cvss_v31 = metrics.get("cvssMetricV31", [])
            if cvss_v31:
                primary = next((m for m in cvss_v31 if m.get("type") == "Primary"), cvss_v31[0])
                cvss_data = primary.get("cvssData", {})
                cvss_score = cvss_data.get("baseScore")
                cvss_vector = cvss_data.get("vectorString")

            # Fall back to CVSS 3.0
            if cvss_score is None:
                cvss_v30 = metrics.get("cvssMetricV30", [])
                if cvss_v30:
                    primary = next((m for m in cvss_v30 if m.get("type") == "Primary"), cvss_v30[0])
                    cvss_data = primary.get("cvssData", {})
                    cvss_score = cvss_data.get("baseScore")
                    cvss_vector = cvss_data.get("vectorString")

            # Fall back to CVSS 2.0
            if cvss_score is None:
                cvss_v2 = metrics.get("cvssMetricV2", [])
                if cvss_v2:
                    primary = next((m for m in cvss_v2 if m.get("type") == "Primary"), cvss_v2[0])
                    cvss_data = primary.get("cvssData", {})
                    cvss_score = cvss_data.get("baseScore")
                    cvss_vector = cvss_data.get("vectorString")

            # Determine severity from CVSS score
            if cvss_score:
                severity = Severity.from_cvss(cvss_score)

            # Get references
            references = []
            for ref in cve_data.get("references", []):
                url = ref.get("url", "")
                if url:
                    references.append(url)

            # Get CWE IDs from weaknesses
            cwe_ids = []
            for weakness in cve_data.get("weaknesses", []):
                for desc in weakness.get("description", []):
                    value = desc.get("value", "")
                    if value.startswith("CWE-"):
                        cwe_ids.append(value)

            # Parse dates
            published = None
            modified = None
            if "published" in cve_data:
                try:
                    published = datetime.fromisoformat(cve_data["published"].replace("Z", "+00:00"))
                except Exception:
                    pass
            if "lastModified" in cve_data:
                try:
                    modified = datetime.fromisoformat(
                        cve_data["lastModified"].replace("Z", "+00:00")
                    )
                except Exception:
                    pass

            # Try to extract affected versions from configurations
            affected_versions = self._extract_affected_versions(cve_data)
            fixed_version = self._extract_fixed_version(cve_data)

            # Create title from first line of description
            title = description.split(".")[0] if description else cve_id
            if len(title) > 100:
                title = title[:97] + "..."

            return Vulnerability(
                id=cve_id,
                aliases=[],  # NVD is the source, CVE is the ID
                severity=severity,
                cvss_score=cvss_score,
                cvss_vector=cvss_vector,
                title=title,
                description=description,
                affected_versions=affected_versions,
                fixed_version=fixed_version,
                source=self.name,
                references=references[:5],  # Limit references
                published=published,
                modified=modified,
                cwe_ids=cwe_ids,
            )

        except Exception as e:
            logger.debug("Error parsing NVD vulnerability: %s", e)
            return None

    def _is_package_affected(self, cve_data: dict, package: Package) -> bool:
        """Check if this CVE actually affects the package.

        NVD keyword search can return false positives, so we verify
        by checking CPE configurations.
        """
        package_name_lower = package.name.lower()

        # Check configurations (CPE matches)
        configurations = cve_data.get("configurations", [])
        for config in configurations:
            for node in config.get("nodes", []):
                for cpe_match in node.get("cpeMatch", []):
                    criteria = cpe_match.get("criteria", "").lower()
                    # Check if package name appears in CPE
                    if package_name_lower in criteria:
                        return True

        # Also check descriptions for package name mention
        descriptions = cve_data.get("descriptions", [])
        for desc in descriptions:
            if package_name_lower in desc.get("value", "").lower():
                return True

        return False

    def _extract_affected_versions(self, cve_data: dict) -> str:
        """Extract affected version range from CPE configurations."""
        versions = []

        configurations = cve_data.get("configurations", [])
        for config in configurations:
            for node in config.get("nodes", []):
                for cpe_match in node.get("cpeMatch", []):
                    if not cpe_match.get("vulnerable", False):
                        continue

                    # Check for version constraints
                    version_start = cpe_match.get("versionStartIncluding")
                    version_end = cpe_match.get("versionEndExcluding")
                    version_end_incl = cpe_match.get("versionEndIncluding")

                    if version_start and version_end:
                        versions.append(f">={version_start}, <{version_end}")
                    elif version_start and version_end_incl:
                        versions.append(f">={version_start}, <={version_end_incl}")
                    elif version_end:
                        versions.append(f"<{version_end}")
                    elif version_end_incl:
                        versions.append(f"<={version_end_incl}")

        if versions:
            return "; ".join(set(versions))
        return ""

    def _extract_fixed_version(self, cve_data: dict) -> str | None:
        """Try to extract fixed version from configurations."""
        configurations = cve_data.get("configurations", [])
        for config in configurations:
            for node in config.get("nodes", []):
                for cpe_match in node.get("cpeMatch", []):
                    version_end = cpe_match.get("versionEndExcluding")
                    if version_end:
                        return version_end
        return None
