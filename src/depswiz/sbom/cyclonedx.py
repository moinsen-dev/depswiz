"""CycloneDX SBOM generation."""

import json
import uuid
from datetime import UTC, datetime
from typing import Any

from depswiz import __version__
from depswiz.core.models import Package


class CycloneDxGenerator:
    """Generator for CycloneDX format SBOMs."""

    def __init__(self, spec_version: str = "1.6"):
        self.spec_version = spec_version

    def generate(
        self,
        packages: list[Package],
        component_name: str = "project",
        component_version: str = "0.0.0",
    ) -> str:
        """Generate a CycloneDX SBOM.

        Args:
            packages: List of packages to include
            component_name: Name of the main component
            component_version: Version of the main component

        Returns:
            JSON string of the CycloneDX SBOM
        """
        serial_number = f"urn:uuid:{uuid.uuid4()}"
        timestamp = datetime.now(UTC).isoformat()

        sbom: dict[str, Any] = {
            "$schema": f"http://cyclonedx.org/schema/bom-{self.spec_version}.schema.json",
            "bomFormat": "CycloneDX",
            "specVersion": self.spec_version,
            "serialNumber": serial_number,
            "version": 1,
            "metadata": {
                "timestamp": timestamp,
                "tools": {
                    "components": [
                        {
                            "type": "application",
                            "name": "depswiz",
                            "version": __version__,
                        }
                    ]
                },
                "component": {
                    "type": "application",
                    "name": component_name,
                    "version": component_version,
                    "bom-ref": f"pkg:{component_name}@{component_version}",
                },
            },
            "components": [],
            "dependencies": [],
        }

        # Add main component dependency
        main_deps = []

        for pkg in packages:
            component = self._package_to_component(pkg)
            sbom["components"].append(component)
            main_deps.append(component["bom-ref"])

        # Add dependency relationship
        sbom["dependencies"].append(
            {
                "ref": f"pkg:{component_name}@{component_version}",
                "dependsOn": main_deps,
            }
        )

        return json.dumps(sbom, indent=2)

    def _package_to_component(self, pkg: Package) -> dict[str, Any]:
        """Convert a Package to a CycloneDX component."""
        purl = self._generate_purl(pkg)
        bom_ref = purl

        component: dict[str, Any] = {
            "type": "library",
            "bom-ref": bom_ref,
            "name": pkg.name,
            "version": pkg.current_version or "unknown",
            "purl": purl,
        }

        # Add license if available
        if pkg.license_info and pkg.license_info.spdx_id:
            component["licenses"] = [{"license": {"id": pkg.license_info.spdx_id}}]

        # Add external references
        external_refs = []

        if pkg.language == "python":
            external_refs.append(
                {
                    "type": "website",
                    "url": f"https://pypi.org/project/{pkg.name}/",
                }
            )
        elif pkg.language == "rust":
            external_refs.append(
                {
                    "type": "website",
                    "url": f"https://crates.io/crates/{pkg.name}",
                }
            )
        elif pkg.language == "javascript":
            external_refs.append(
                {
                    "type": "website",
                    "url": f"https://www.npmjs.com/package/{pkg.name}",
                }
            )
        elif pkg.language == "dart":
            external_refs.append(
                {
                    "type": "website",
                    "url": f"https://pub.dev/packages/{pkg.name}",
                }
            )

        if external_refs:
            component["externalReferences"] = external_refs

        # Add properties for additional metadata
        properties = []

        if pkg.is_dev:
            properties.append(
                {
                    "name": "depswiz:scope",
                    "value": "development",
                }
            )

        if pkg.language:
            properties.append(
                {
                    "name": "depswiz:language",
                    "value": pkg.language,
                }
            )

        if properties:
            component["properties"] = properties

        return component

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
            # @scope/name -> pkg:npm/%40scope/name
            name = pkg.name.replace("@", "%40").replace("/", "%2F")
        else:
            name = pkg.name

        return f"pkg:{purl_type}/{name}@{version}"
