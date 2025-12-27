# Developing Plugins

This guide explains how to create a new language plugin for depswiz.

## Overview

A language plugin consists of:

1. **Plugin class** implementing `LanguagePlugin` interface
2. **Manifest parser** to read dependency specifications
3. **Lockfile parser** (optional) to read resolved versions
4. **Registry client** to fetch latest versions
5. **Entry point registration** in pyproject.toml

## Quick Start

### 1. Create Plugin Structure

```
my-depswiz-plugin/
├── pyproject.toml
├── src/
│   └── depswiz_mylang/
│       ├── __init__.py
│       └── plugin.py
└── tests/
    └── test_plugin.py
```

### 2. Implement the Plugin

```python
# src/depswiz_mylang/plugin.py

from pathlib import Path
from depswiz.plugins.base import LanguagePlugin
from depswiz.core.models import Package, Vulnerability, LicenseInfo


class MyLangPlugin(LanguagePlugin):
    """Plugin for MyLang package manager."""

    @property
    def name(self) -> str:
        return "mylang"

    @property
    def display_name(self) -> str:
        return "My Language"

    @property
    def manifest_patterns(self) -> list[str]:
        return ["mylang.toml", "mylang.json"]

    @property
    def lockfile_patterns(self) -> list[str]:
        return ["mylang.lock"]

    def detect(self, path: Path) -> bool:
        """Check if this plugin should handle the given directory."""
        for pattern in self.manifest_patterns:
            if (path / pattern).exists():
                return True
        return False

    def parse_manifest(self, path: Path) -> list[Package]:
        """Parse manifest file and return list of dependencies."""
        manifest_path = path / "mylang.toml"
        # Parse your manifest format
        packages = []
        # ... parsing logic ...
        return packages

    def parse_lockfile(self, path: Path) -> list[Package]:
        """Parse lockfile and return resolved dependencies."""
        lockfile_path = path / "mylang.lock"
        if not lockfile_path.exists():
            return []
        # ... parsing logic ...
        return []

    async def fetch_latest_version(self, package: Package) -> str | None:
        """Fetch the latest version from the package registry."""
        # Query your package registry
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://registry.mylang.dev/api/packages/{package.name}"
            )
            if response.status_code == 200:
                data = response.json()
                return data["latest_version"]
        return None

    async def fetch_vulnerabilities(
        self, package: Package
    ) -> list[Vulnerability]:
        """Fetch known vulnerabilities for a package."""
        # Query vulnerability databases
        return []

    async def fetch_license(self, package: Package) -> LicenseInfo | None:
        """Fetch license information for a package."""
        return None

    def generate_update_command(self, packages: list[Package]) -> list[str]:
        """Generate shell command to update packages."""
        if not packages:
            return []
        pkg_specs = [f"{p.name}@{p.latest_version}" for p in packages]
        return ["mylang", "update"] + pkg_specs
```

### 3. Register the Plugin

```toml
# pyproject.toml

[project]
name = "depswiz-mylang"
version = "0.1.0"
dependencies = ["depswiz>=0.2.0"]

[project.entry-points."depswiz.languages"]
mylang = "depswiz_mylang:MyLangPlugin"
```

### 4. Export from __init__.py

```python
# src/depswiz_mylang/__init__.py

from depswiz_mylang.plugin import MyLangPlugin

__all__ = ["MyLangPlugin"]
```

## Plugin Interface

### Required Methods

| Method | Description |
|--------|-------------|
| `name` | Short identifier (e.g., "python") |
| `display_name` | Human-readable name (e.g., "Python") |
| `manifest_patterns` | List of manifest file patterns |
| `detect(path)` | Check if plugin handles this directory |
| `parse_manifest(path)` | Parse dependencies from manifest |
| `fetch_latest_version(package)` | Get latest version from registry |

### Optional Methods

| Method | Description | Default |
|--------|-------------|---------|
| `lockfile_patterns` | List of lockfile patterns | `[]` |
| `parse_lockfile(path)` | Parse resolved versions | `[]` |
| `fetch_vulnerabilities(package)` | Get known CVEs | `[]` |
| `fetch_license(package)` | Get license info | `None` |
| `generate_update_command(packages)` | Update command | `[]` |
| `detect_workspace(path)` | Find workspace members | `[]` |

## Data Models

### Package

```python
from dataclasses import dataclass
from depswiz.core.models import UpdateType

@dataclass
class Package:
    name: str
    current_version: str
    latest_version: str | None = None
    update_type: UpdateType | None = None
    language: str = ""
    is_dev: bool = False
    is_transitive: bool = False
```

### Vulnerability

```python
@dataclass
class Vulnerability:
    id: str  # CVE-2024-XXXXX
    package: str
    severity: Severity  # LOW, MEDIUM, HIGH, CRITICAL
    description: str
    fixed_version: str | None = None
    references: list[str] = field(default_factory=list)
```

### LicenseInfo

```python
@dataclass
class LicenseInfo:
    spdx_id: str  # MIT, Apache-2.0, etc.
    name: str
    url: str | None = None
```

## Testing Your Plugin

```python
# tests/test_plugin.py

import pytest
from pathlib import Path
from depswiz_mylang import MyLangPlugin


@pytest.fixture
def plugin():
    return MyLangPlugin()


def test_name(plugin):
    assert plugin.name == "mylang"


def test_detect(plugin, tmp_path):
    # Create manifest file
    (tmp_path / "mylang.toml").write_text("[dependencies]")
    assert plugin.detect(tmp_path) is True


def test_parse_manifest(plugin, tmp_path):
    manifest = """
    [dependencies]
    my-package = "1.0.0"
    """
    (tmp_path / "mylang.toml").write_text(manifest)
    packages = plugin.parse_manifest(tmp_path)
    assert len(packages) == 1
    assert packages[0].name == "my-package"


@pytest.mark.asyncio
async def test_fetch_latest_version(plugin):
    from depswiz.core.models import Package
    pkg = Package(name="my-package", current_version="1.0.0")
    version = await plugin.fetch_latest_version(pkg)
    assert version is not None
```

## Best Practices

### 1. Async HTTP Calls

Use `httpx.AsyncClient` for registry queries:

```python
async def fetch_latest_version(self, package: Package) -> str | None:
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=10.0)
```

### 2. Caching

Use depswiz's disk cache for registry responses:

```python
from depswiz.core.cache import cache

@cache.memoize(expire=3600)  # Cache for 1 hour
async def fetch_package_info(self, name: str):
    # ... fetch from registry ...
```

### 3. Error Handling

Handle network and parsing errors gracefully:

```python
async def fetch_latest_version(self, package: Package) -> str | None:
    try:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()["version"]
    except (httpx.HTTPError, KeyError):
        return None
```

### 4. Version Parsing

Use semantic versioning for comparison:

```python
from packaging.version import Version

def compare_versions(current: str, latest: str) -> UpdateType:
    curr = Version(current)
    late = Version(latest)
    if late.major > curr.major:
        return UpdateType.MAJOR
    elif late.minor > curr.minor:
        return UpdateType.MINOR
    elif late.micro > curr.micro:
        return UpdateType.PATCH
    return UpdateType.UP_TO_DATE
```

## Publishing

1. Test your plugin thoroughly
2. Add documentation
3. Publish to PyPI:

```bash
uv build
uv publish
```

Users can then install:

```bash
pip install depswiz-mylang
```

depswiz will automatically discover and use the plugin.

## See Also

- [Plugin API Reference](api.md)
- [Built-in Plugins Source](https://github.com/moinsen-dev/depswiz/tree/main/src/depswiz/plugins)
