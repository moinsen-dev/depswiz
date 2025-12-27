"""SBOM generation module for depswiz."""

from depswiz.sbom.cyclonedx import CycloneDxGenerator
from depswiz.sbom.spdx import SpdxGenerator

__all__ = ["CycloneDxGenerator", "SpdxGenerator"]
