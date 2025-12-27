# Plugin API Reference

Complete API documentation for developing depswiz language plugins.

## LanguagePlugin (Abstract Base Class)

The base class that all language plugins must inherit from.

```python
from abc import ABC, abstractmethod
from pathlib import Path
from depswiz.core.models import Package, Vulnerability, LicenseInfo


class LanguagePlugin(ABC):
    """Abstract base class for language plugins."""
```

### Required Properties

#### name

```python
@property
@abstractmethod
def name(self) -> str:
    """Short identifier for this language.

    Used in CLI flags and configuration.

    Returns:
        Short name like "python", "rust", "dart"

    Example:
        >>> plugin.name
        'python'
    """
```

#### display_name

```python
@property
@abstractmethod
def display_name(self) -> str:
    """Human-readable name for display.

    Returns:
        Display name like "Python", "Rust", "Dart/Flutter"

    Example:
        >>> plugin.display_name
        'Python'
    """
```

#### manifest_patterns

```python
@property
@abstractmethod
def manifest_patterns(self) -> list[str]:
    """File patterns that indicate this language.

    Returns:
        List of manifest file names or glob patterns

    Example:
        >>> plugin.manifest_patterns
        ['pyproject.toml', 'requirements.txt', 'setup.py']
    """
```

### Required Methods

#### detect

```python
@abstractmethod
def detect(self, path: Path) -> bool:
    """Check if this plugin should handle the given directory.

    Args:
        path: Directory path to check

    Returns:
        True if this plugin's manifest files exist

    Example:
        >>> plugin.detect(Path("/my/python/project"))
        True
    """
```

#### parse_manifest

```python
@abstractmethod
def parse_manifest(self, path: Path) -> list[Package]:
    """Parse manifest file and extract dependencies.

    Args:
        path: Directory containing manifest file

    Returns:
        List of Package objects with current versions

    Raises:
        FileNotFoundError: If manifest doesn't exist
        ParseError: If manifest is malformed

    Example:
        >>> packages = plugin.parse_manifest(Path("."))
        >>> packages[0].name
        'httpx'
    """
```

#### fetch_latest_version

```python
@abstractmethod
async def fetch_latest_version(self, package: Package) -> str | None:
    """Fetch latest version from package registry.

    Args:
        package: Package to look up

    Returns:
        Latest version string, or None if not found

    Example:
        >>> await plugin.fetch_latest_version(pkg)
        '0.28.1'
    """
```

### Optional Properties

#### lockfile_patterns

```python
@property
def lockfile_patterns(self) -> list[str]:
    """Lockfile patterns for this language.

    Returns:
        List of lockfile names, empty if not applicable

    Example:
        >>> plugin.lockfile_patterns
        ['uv.lock', 'poetry.lock']
    """
    return []
```

### Optional Methods

#### parse_lockfile

```python
def parse_lockfile(self, path: Path) -> list[Package]:
    """Parse lockfile for resolved versions.

    Args:
        path: Directory containing lockfile

    Returns:
        List of packages with resolved versions
    """
    return []
```

#### fetch_vulnerabilities

```python
async def fetch_vulnerabilities(
    self, package: Package
) -> list[Vulnerability]:
    """Fetch known vulnerabilities for a package.

    Args:
        package: Package to check

    Returns:
        List of known vulnerabilities
    """
    return []
```

#### fetch_license

```python
async def fetch_license(self, package: Package) -> LicenseInfo | None:
    """Fetch license information for a package.

    Args:
        package: Package to look up

    Returns:
        License info, or None if unknown
    """
    return None
```

#### generate_update_command

```python
def generate_update_command(self, packages: list[Package]) -> list[str]:
    """Generate shell command to update packages.

    Args:
        packages: Packages to update

    Returns:
        Command as list of arguments

    Example:
        >>> plugin.generate_update_command(packages)
        ['pip', 'install', 'httpx==0.28.1', 'rich==13.9.4']
    """
    return []
```

#### detect_workspace

```python
def detect_workspace(self, path: Path) -> list[Path]:
    """Detect workspace members for monorepo support.

    Args:
        path: Root directory to scan

    Returns:
        List of workspace member paths
    """
    return []
```

## Data Models

### Package

```python
from dataclasses import dataclass, field
from enum import Enum


class UpdateType(Enum):
    """Type of version update."""
    UP_TO_DATE = "up_to_date"
    PATCH = "patch"
    MINOR = "minor"
    MAJOR = "major"
    UNKNOWN = "unknown"


@dataclass
class Package:
    """Represents a package dependency."""

    name: str
    """Package name"""

    current_version: str
    """Currently installed/specified version"""

    latest_version: str | None = None
    """Latest available version from registry"""

    update_type: UpdateType | None = None
    """Type of update (patch, minor, major)"""

    language: str = ""
    """Language/ecosystem (python, rust, etc.)"""

    is_dev: bool = False
    """True if this is a dev dependency"""

    is_transitive: bool = False
    """True if this is a transitive (indirect) dependency"""

    version_constraint: str | None = None
    """Original version constraint (>=1.0.0, ^2.0)"""

    homepage: str | None = None
    """Package homepage URL"""

    repository: str | None = None
    """Source repository URL"""
```

### Vulnerability

```python
class Severity(Enum):
    """Vulnerability severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Vulnerability:
    """Represents a security vulnerability."""

    id: str
    """CVE or advisory ID (e.g., CVE-2024-12345)"""

    package: str
    """Affected package name"""

    severity: Severity
    """Severity level"""

    description: str
    """Human-readable description"""

    affected_versions: str | None = None
    """Affected version range (e.g., <1.5.0)"""

    fixed_version: str | None = None
    """Version that fixes the vulnerability"""

    references: list[str] = field(default_factory=list)
    """Reference URLs (NVD, advisory pages)"""

    published: str | None = None
    """Publication date (ISO format)"""
```

### LicenseInfo

```python
@dataclass
class LicenseInfo:
    """Package license information."""

    spdx_id: str
    """SPDX license identifier (e.g., MIT, Apache-2.0)"""

    name: str
    """Full license name"""

    url: str | None = None
    """URL to license text"""

    is_osi_approved: bool = False
    """True if OSI approved"""

    is_copyleft: bool = False
    """True if copyleft license"""
```

## Helper Classes

### RegistryClient

Base class for registry API clients:

```python
from depswiz.plugins.registry import RegistryClient


class MyRegistryClient(RegistryClient):
    """Client for MyLang package registry."""

    base_url = "https://registry.mylang.dev/api"

    async def get_package(self, name: str) -> dict:
        """Fetch package metadata."""
        return await self.get(f"/packages/{name}")

    async def get_latest_version(self, name: str) -> str:
        """Get latest version."""
        data = await self.get_package(name)
        return data["latest_version"]
```

### ManifestParser

Base class for manifest parsing:

```python
from depswiz.plugins.parser import ManifestParser


class MyManifestParser(ManifestParser):
    """Parser for mylang.toml files."""

    def parse(self, content: str) -> list[Package]:
        """Parse manifest content."""
        # ... parsing logic ...
        return packages
```

## Error Classes

```python
from depswiz.core.errors import DepswizError


class PluginError(DepswizError):
    """Base error for plugin issues."""


class ParseError(PluginError):
    """Error parsing manifest or lockfile."""


class RegistryError(PluginError):
    """Error communicating with package registry."""


class PackageNotFoundError(PluginError):
    """Package not found in registry."""
```

## Plugin Registry

Access the plugin registry:

```python
from depswiz.plugins.registry import get_plugin, list_plugins


# Get specific plugin
python_plugin = get_plugin("python")

# List all available plugins
for plugin in list_plugins():
    print(f"{plugin.name}: {plugin.display_name}")
```

## See Also

- [Developing Plugins](developing.md) - Tutorial for creating plugins
- [Source Code](https://github.com/moinsen-dev/depswiz/tree/main/src/depswiz/plugins)
