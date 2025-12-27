"""GitHub Security Advisories (GHSA) data source."""

import os
from datetime import datetime

import httpx

from depswiz.core.logging import get_logger
from depswiz.core.models import Package, Severity, Vulnerability
from depswiz.security.sources.base import VulnerabilitySource

logger = get_logger("security.ghsa")

# Mapping from plugin names to GHSA ecosystem names
ECOSYSTEM_MAP = {
    "python": "PIP",
    "rust": "RUST",
    "dart": "PUB",
    "javascript": "NPM",
}


class GhsaSource(VulnerabilitySource):
    """GitHub Security Advisories vulnerability database source.

    Uses the GitHub GraphQL API to query security advisories.
    Requires a GITHUB_TOKEN environment variable for higher rate limits.
    """

    GRAPHQL_URL = "https://api.github.com/graphql"

    # GraphQL query to fetch security advisories for a package
    QUERY = """
    query($ecosystem: SecurityAdvisoryEcosystem!, $package: String!) {
      securityVulnerabilities(
        first: 20,
        ecosystem: $ecosystem,
        package: $package
      ) {
        nodes {
          advisory {
            ghsaId
            summary
            description
            severity
            cvss {
              score
              vectorString
            }
            publishedAt
            updatedAt
            references {
              url
            }
            cwes(first: 5) {
              nodes {
                cweId
              }
            }
            identifiers {
              type
              value
            }
          }
          vulnerableVersionRange
          firstPatchedVersion {
            identifier
          }
        }
      }
    }
    """

    @property
    def name(self) -> str:
        return "ghsa"

    @property
    def display_name(self) -> str:
        return "GitHub Security Advisories"

    def _get_github_token(self) -> str | None:
        """Get GitHub token from environment."""
        return os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")

    async def check_package(
        self, client: httpx.AsyncClient, package: Package
    ) -> list[Vulnerability]:
        """Query GHSA for vulnerabilities affecting a package."""
        if not package.current_version or not package.language:
            return []

        ecosystem = ECOSYSTEM_MAP.get(package.language)
        if not ecosystem:
            return []

        token = self._get_github_token()
        if not token:
            logger.debug("No GitHub token available, skipping GHSA check for %s", package.name)
            return []

        try:
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }

            payload = {
                "query": self.QUERY,
                "variables": {
                    "ecosystem": ecosystem,
                    "package": package.name,
                },
            }

            response = await client.post(
                self.GRAPHQL_URL,
                headers=headers,
                json=payload,
                timeout=30.0,
            )

            if response.status_code != 200:
                logger.debug("GHSA returned status %d for %s", response.status_code, package.name)
                return []

            data = response.json()

            # Check for GraphQL errors
            if "errors" in data:
                logger.debug("GHSA GraphQL errors for %s: %s", package.name, data["errors"])
                return []

            vulns = []
            nodes = data.get("data", {}).get("securityVulnerabilities", {}).get("nodes", [])

            for node in nodes:
                vuln = self._parse_vulnerability(node, package.current_version)
                if vuln:
                    vulns.append(vuln)

            return vulns

        except httpx.HTTPStatusError as e:
            logger.debug("HTTP error querying GHSA for %s: %s", package.name, e)
        except httpx.RequestError as e:
            logger.debug("Request error querying GHSA for %s: %s", package.name, e)
        except Exception as e:
            logger.debug("Unexpected error querying GHSA for %s: %s", package.name, e)

        return []

    def _parse_vulnerability(self, node: dict, current_version: str) -> Vulnerability | None:
        """Parse GHSA vulnerability data into our model."""
        try:
            advisory = node.get("advisory", {})
            vuln_id = advisory.get("ghsaId", "")

            if not vuln_id:
                return None

            # Check if current version is in vulnerable range
            version_range = node.get("vulnerableVersionRange", "")
            if not self._is_version_vulnerable(current_version, version_range):
                return None

            # Extract severity
            severity_str = advisory.get("severity", "").upper()
            severity = Severity.UNKNOWN
            if severity_str in ("CRITICAL", "HIGH", "MEDIUM", "MODERATE", "LOW"):
                if severity_str == "MODERATE":
                    severity_str = "MEDIUM"
                severity = Severity[severity_str]

            # CVSS info
            cvss_data = advisory.get("cvss", {})
            cvss_score = cvss_data.get("score")
            cvss_vector = cvss_data.get("vectorString")

            # If we have CVSS score, override severity from that
            if cvss_score:
                severity = Severity.from_cvss(cvss_score)

            # Get fixed version
            fixed_info = node.get("firstPatchedVersion", {})
            fixed_version = fixed_info.get("identifier") if fixed_info else None

            # Get aliases (CVE IDs)
            aliases = []
            for identifier in advisory.get("identifiers", []):
                if identifier.get("type") == "CVE":
                    aliases.append(identifier.get("value"))

            # Get references
            references = [
                ref.get("url", "") for ref in advisory.get("references", []) if ref.get("url")
            ]

            # Get CWE IDs
            cwe_ids = [
                cwe.get("cweId", "")
                for cwe in advisory.get("cwes", {}).get("nodes", [])
                if cwe.get("cweId")
            ]

            # Parse dates
            published = None
            modified = None
            if "publishedAt" in advisory:
                try:
                    published = datetime.fromisoformat(
                        advisory["publishedAt"].replace("Z", "+00:00")
                    )
                except Exception:
                    pass
            if "updatedAt" in advisory:
                try:
                    modified = datetime.fromisoformat(advisory["updatedAt"].replace("Z", "+00:00"))
                except Exception:
                    pass

            return Vulnerability(
                id=vuln_id,
                aliases=aliases,
                severity=severity,
                cvss_score=cvss_score,
                cvss_vector=cvss_vector,
                title=advisory.get("summary", vuln_id),
                description=advisory.get("description", ""),
                affected_versions=version_range,
                fixed_version=fixed_version,
                source=self.name,
                references=references[:5],  # Limit references
                published=published,
                modified=modified,
                cwe_ids=cwe_ids,
            )

        except Exception as e:
            logger.debug("Error parsing GHSA vulnerability: %s", e)
            return None

    def _is_version_vulnerable(self, current: str, version_range: str) -> bool:
        """Check if current version falls within vulnerable range.

        GHSA uses semver-style ranges like:
        - "< 1.2.3"
        - ">= 1.0.0, < 2.0.0"
        - "= 1.2.3"

        For simplicity, we'll be conservative and return True if we can't
        definitively determine the version is NOT vulnerable.
        """
        if not version_range or not current:
            return True

        try:
            from packaging.version import Version

            current_ver = Version(current)

            # Parse version range constraints
            constraints = [c.strip() for c in version_range.split(",")]

            for constraint in constraints:
                constraint = constraint.strip()

                if constraint.startswith(">="):
                    min_ver = Version(constraint[2:].strip())
                    if current_ver < min_ver:
                        return False
                elif constraint.startswith(">"):
                    min_ver = Version(constraint[1:].strip())
                    if current_ver <= min_ver:
                        return False
                elif constraint.startswith("<="):
                    max_ver = Version(constraint[2:].strip())
                    if current_ver > max_ver:
                        return False
                elif constraint.startswith("<"):
                    max_ver = Version(constraint[1:].strip())
                    if current_ver >= max_ver:
                        return False
                elif constraint.startswith("="):
                    exact_ver = Version(constraint[1:].strip())
                    if current_ver != exact_ver:
                        return False

            return True

        except Exception:
            # If we can't parse, assume vulnerable to be safe
            return True
