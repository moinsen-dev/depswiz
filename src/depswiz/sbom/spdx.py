"""SPDX SBOM generation."""

import json
import uuid
from datetime import UTC, datetime
from typing import Any

from depswiz import __version__
from depswiz.core.models import Package


class SpdxGenerator:
    """Generator for SPDX format SBOMs."""

    def __init__(self, spec_version: str = "3.0"):
        self.spec_version = spec_version

    def generate(
        self,
        packages: list[Package],
        component_name: str = "project",
        component_version: str = "0.0.0",
    ) -> str:
        """Generate an SPDX SBOM.

        Args:
            packages: List of packages to include
            component_name: Name of the main component
            component_version: Version of the main component

        Returns:
            JSON string of the SPDX SBOM
        """
        doc_id = str(uuid.uuid4())
        timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

        # Generate unique SPDX IDs
        doc_spdxid = "SPDXRef-DOCUMENT"
        main_spdxid = f"SPDXRef-Package-{self._sanitize_id(component_name)}"

        sbom: dict[str, Any] = {
            "spdxVersion": f"SPDX-{self.spec_version}",
            "dataLicense": "CC0-1.0",
            "SPDXID": doc_spdxid,
            "name": f"{component_name}-sbom",
            "documentNamespace": f"https://depswiz.dev/sbom/{doc_id}",
            "creationInfo": {
                "created": timestamp,
                "creators": [
                    f"Tool: depswiz-{__version__}",
                ],
            },
            "packages": [],
            "relationships": [],
        }

        # Add main package
        main_package = {
            "SPDXID": main_spdxid,
            "name": component_name,
            "versionInfo": component_version,
            "downloadLocation": "NOASSERTION",
            "filesAnalyzed": False,
            "primaryPackagePurpose": "APPLICATION",
        }
        sbom["packages"].append(main_package)

        # Add document describes relationship
        sbom["relationships"].append(
            {
                "spdxElementId": doc_spdxid,
                "relationshipType": "DESCRIBES",
                "relatedSpdxElement": main_spdxid,
            }
        )

        # Add dependency packages
        for pkg in packages:
            pkg_data = self._package_to_spdx(pkg)
            sbom["packages"].append(pkg_data)

            # Add dependency relationship
            sbom["relationships"].append(
                {
                    "spdxElementId": main_spdxid,
                    "relationshipType": "DEPENDS_ON",
                    "relatedSpdxElement": pkg_data["SPDXID"],
                }
            )

        return json.dumps(sbom, indent=2)

    def _package_to_spdx(self, pkg: Package) -> dict[str, Any]:
        """Convert a Package to an SPDX package entry."""
        spdxid = f"SPDXRef-Package-{self._sanitize_id(pkg.name)}"
        purl = self._generate_purl(pkg)

        package = {
            "SPDXID": spdxid,
            "name": pkg.name,
            "versionInfo": pkg.current_version or "NOASSERTION",
            "downloadLocation": self._get_download_location(pkg),
            "filesAnalyzed": False,
            "primaryPackagePurpose": "LIBRARY",
            "externalRefs": [
                {
                    "referenceCategory": "PACKAGE-MANAGER",
                    "referenceType": "purl",
                    "referenceLocator": purl,
                }
            ],
        }

        # Add license information
        if pkg.license_info and pkg.license_info.spdx_id:
            package["licenseConcluded"] = pkg.license_info.spdx_id
            package["licenseDeclared"] = pkg.license_info.spdx_id
        else:
            package["licenseConcluded"] = "NOASSERTION"
            package["licenseDeclared"] = "NOASSERTION"

        # Add supplier if known
        if pkg.language:
            supplier_map = {
                "python": "PyPI (https://pypi.org)",
                "rust": "crates.io (https://crates.io)",
                "javascript": "npm (https://www.npmjs.com)",
                "dart": "pub.dev (https://pub.dev)",
            }
            supplier = supplier_map.get(pkg.language)
            if supplier:
                package["supplier"] = f"Organization: {supplier}"

        return package

    def _sanitize_id(self, name: str) -> str:
        """Sanitize a name for use in SPDX IDs."""
        # SPDX IDs can only contain letters, numbers, dots, and hyphens
        import re

        sanitized = re.sub(r"[^a-zA-Z0-9.-]", "-", name)
        # Remove consecutive hyphens
        sanitized = re.sub(r"-+", "-", sanitized)
        # Remove leading/trailing hyphens
        sanitized = sanitized.strip("-")
        return sanitized or "unknown"

    def _generate_purl(self, pkg: Package) -> str:
        """Generate a Package URL (PURL) for a package."""
        purl_type_map = {
            "python": "pypi",
            "rust": "cargo",
            "javascript": "npm",
            "dart": "pub",
        }

        purl_type = purl_type_map.get(pkg.language or "", "generic")
        version = pkg.current_version or "0.0.0"

        # Handle scoped packages for npm
        if purl_type == "npm" and pkg.name.startswith("@"):
            name = pkg.name.replace("@", "%40").replace("/", "%2F")
        else:
            name = pkg.name

        return f"pkg:{purl_type}/{name}@{version}"

    def _get_download_location(self, pkg: Package) -> str:
        """Get the download location URL for a package."""
        version = pkg.current_version or ""

        if pkg.language == "python":
            return f"https://pypi.org/project/{pkg.name}/{version}/"
        elif pkg.language == "rust":
            return f"https://crates.io/crates/{pkg.name}/{version}"
        elif pkg.language == "javascript":
            return f"https://registry.npmjs.org/{pkg.name}/-/{pkg.name}-{version}.tgz"
        elif pkg.language == "dart":
            return f"https://pub.dev/packages/{pkg.name}/versions/{version}"

        return "NOASSERTION"
