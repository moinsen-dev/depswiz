"""OSV (Open Source Vulnerabilities) data source."""

from datetime import datetime

import httpx

from depswiz.core.logging import get_logger
from depswiz.core.models import Package, Severity, Vulnerability
from depswiz.security.sources.base import VulnerabilitySource

logger = get_logger("security.osv")

# Mapping from plugin names to OSV ecosystem names
ECOSYSTEM_MAP = {
    "python": "PyPI",
    "rust": "crates.io",
    "dart": "Pub",
    "javascript": "npm",
    "golang": "Go",
}


class OsvSource(VulnerabilitySource):
    """OSV vulnerability database source."""

    OSV_API = "https://api.osv.dev/v1/query"

    @property
    def name(self) -> str:
        return "osv"

    @property
    def display_name(self) -> str:
        return "Open Source Vulnerabilities (OSV)"

    async def check_package(
        self, client: httpx.AsyncClient, package: Package
    ) -> list[Vulnerability]:
        """Query OSV for vulnerabilities affecting a package."""
        if not package.current_version or not package.language:
            return []

        ecosystem = ECOSYSTEM_MAP.get(package.language)
        if not ecosystem:
            return []

        try:
            payload = {
                "package": {
                    "name": package.name,
                    "ecosystem": ecosystem,
                },
                "version": package.current_version,
            }

            response = await client.post(
                self.OSV_API,
                json=payload,
                timeout=30.0,
            )

            if response.status_code != 200:
                return []

            data = response.json()
            vulns = []

            for vuln_data in data.get("vulns", []):
                vuln = self._parse_vulnerability(vuln_data)
                if vuln:
                    vulns.append(vuln)

            return vulns

        except httpx.HTTPStatusError as e:
            logger.debug("HTTP error querying OSV for %s: %s", package.name, e)
        except httpx.RequestError as e:
            logger.debug("Request error querying OSV for %s: %s", package.name, e)
        except Exception as e:
            logger.debug("Unexpected error querying OSV for %s: %s", package.name, e)

        return []

    def _parse_vulnerability(self, data: dict) -> Vulnerability | None:
        """Parse OSV vulnerability data into our model."""
        try:
            vuln_id = data.get("id", "")
            aliases = data.get("aliases", [])

            # Extract severity
            severity = Severity.UNKNOWN
            cvss_score = None
            cvss_vector = None

            for sev_data in data.get("severity", []):
                if sev_data.get("type") == "CVSS_V3":
                    cvss_vector = sev_data.get("score", "")
                    # Parse CVSS score from vector if present
                    score = self._parse_cvss_score(cvss_vector)
                    if score:
                        cvss_score = score
                        severity = Severity.from_cvss(score)

            # If no CVSS, try database_specific
            if severity == Severity.UNKNOWN:
                db_specific = data.get("database_specific", {})
                sev_str = db_specific.get("severity", "").upper()
                if sev_str in ("CRITICAL", "HIGH", "MEDIUM", "MODERATE", "LOW"):
                    if sev_str == "MODERATE":
                        sev_str = "MEDIUM"
                    severity = Severity[sev_str]

            # Extract affected versions and fixed version
            affected_str = ""
            fixed_version = None

            for affected in data.get("affected", []):
                ranges = affected.get("ranges", [])
                for range_data in ranges:
                    events = range_data.get("events", [])
                    for event in events:
                        if "introduced" in event:
                            introduced = event["introduced"]
                            if introduced != "0":
                                affected_str += f">={introduced} "
                        if "fixed" in event:
                            fixed_version = event["fixed"]
                            affected_str += f"<{fixed_version} "

                # Also check versions array
                versions = affected.get("versions", [])
                if versions and not affected_str:
                    affected_str = ", ".join(versions[:5])
                    if len(versions) > 5:
                        affected_str += f" (+{len(versions) - 5} more)"

            # Get references
            references = [
                ref.get("url", "") for ref in data.get("references", []) if ref.get("url")
            ]

            # Parse dates
            published = None
            modified = None
            if "published" in data:
                try:
                    published = datetime.fromisoformat(data["published"].replace("Z", "+00:00"))
                except Exception:
                    pass
            if "modified" in data:
                try:
                    modified = datetime.fromisoformat(data["modified"].replace("Z", "+00:00"))
                except Exception:
                    pass

            # Get CWE IDs
            cwe_ids = []
            for ref in data.get("references", []):
                url = ref.get("url", "")
                if "cwe.mitre.org" in url:
                    # Extract CWE ID from URL
                    import re

                    match = re.search(r"CWE-(\d+)", url)
                    if match:
                        cwe_ids.append(f"CWE-{match.group(1)}")

            return Vulnerability(
                id=vuln_id,
                aliases=aliases,
                severity=severity,
                cvss_score=cvss_score,
                cvss_vector=cvss_vector,
                title=data.get("summary", data.get("id", "")),
                description=data.get("details", ""),
                affected_versions=affected_str.strip(),
                fixed_version=fixed_version,
                source=self.name,
                references=references[:5],  # Limit references
                published=published,
                modified=modified,
                cwe_ids=cwe_ids,
            )

        except Exception as e:
            logger.debug("Error parsing vulnerability data: %s", e)
            return None

    def _parse_cvss_score(self, vector: str) -> float | None:
        """Extract CVSS score from a CVSS vector string."""
        if not vector:
            return None

        # Try to find score in common formats

        # CVSS:3.1/AV:N/AC:L/... format doesn't include score
        # We need to calculate or estimate

        # Check if it's just a score
        try:
            score = float(vector)
            if 0 <= score <= 10:
                return score
        except ValueError:
            pass

        # Basic estimation from attack vector
        if "AV:N" in vector:
            base = 7.0
        elif "AV:A" in vector:
            base = 5.5
        elif "AV:L" in vector:
            base = 4.0
        else:
            base = 3.0

        # Adjust for attack complexity
        if "AC:L" in vector:
            base += 1.5
        elif "AC:H" in vector:
            base -= 1.0

        # Adjust for privileges required
        if "PR:N" in vector:
            base += 1.0
        elif "PR:H" in vector:
            base -= 0.5

        return min(10.0, max(0.0, base))
