# depswiz - Product Requirements Document

## Version 1.0

---

## 1. Executive Summary

**depswiz** (Dependency Wizard) is a next-generation, multi-language dependency management CLI tool designed for modern development workflows. Built on Python 3.13+ with Typer and Rich, it provides a unified interface for checking, auditing, and updating dependencies across Python, Rust, Dart/Flutter, and TypeScript/JavaScript ecosystems.

The tool extends beyond simple version checking to offer a comprehensive security-first approach: vulnerability scanning via OSV/NVD/GitHub Advisories, license compliance verification, SBOM generation in CycloneDX and SPDX formats, and intelligent monorepo support. Its plugin architecture ensures extensibility, allowing the community to add support for additional languages and registries.

### Key Differentiators

- **Multi-language support** with consistent UX across ecosystems
- **Security-first design** with integrated vulnerability and license scanning
- **Standards-compliant SBOM generation** (CycloneDX 1.6, SPDX 3.0)
- **Extensible plugin architecture** via Python entry_points
- **Modern CLI experience** with Rich formatting and progressive disclosure
- **Intelligent monorepo detection** and aggregated reporting

---

## 2. Problem Statement

### Current Pain Points

**Fragmented Tooling:** Developers working across multiple languages must learn and configure disparate tools (pip-audit, cargo-audit, npm audit, etc.) with inconsistent interfaces, output formats, and capabilities.

**Security Blind Spots:** Existing solutions focus solely on version updates, missing critical security concerns:
- No vulnerability database integration
- No license compliance checking
- No SBOM generation for supply chain audits

**Monorepo Complexity:** Modern projects often span multiple languages (e.g., Flutter frontend + Rust FFI + Python ML backend). Current tools operate in silos, requiring manual aggregation of security and update status.

**Compliance Requirements:** Organizations increasingly require:
- Software Bill of Materials for supply chain transparency
- License audits for legal compliance
- Vulnerability reports for security compliance (SOC2, ISO 27001)

---

## 3. Goals and Non-Goals

### Goals (v1.0)

| Priority | Goal | Success Criteria |
|----------|------|------------------|
| P0 | Multi-language dependency checking | Support Python, Rust, Dart, JS/TS ecosystems |
| P0 | Vulnerability scanning | Integrate OSV, GitHub Advisories, RustSec |
| P0 | Plugin architecture | Third-party plugins installable via pip |
| P1 | SBOM generation | CycloneDX 1.6 and SPDX 3.0 compliance |
| P1 | License compliance | SPDX-based license checking with policies |
| P1 | Multiple output formats | CLI, JSON, Markdown, HTML |
| P1 | Monorepo support | Auto-detect workspaces, aggregated reports |
| P2 | Auto-update capability | Interactive updates with confirmation |
| P2 | Breaking change detection | Warn on major version bumps |
| P2 | CI/CD integration | Exit codes, machine-readable output |

### Non-Goals (v1.0)

- **Dependency resolution**: We check versions, not resolve conflicts (defer to native tools)
- **Package installation**: We advise, not install (user runs pip/cargo/npm)
- **Private registry authentication management**: Users configure credentials externally
- **Transitive dependency updates**: Focus on direct dependencies; transitives via lockfiles
- **Real-time monitoring/webhooks**: Batch-mode CLI, not a service
- **IDE plugins**: CLI-first; IDE integration is future scope

---

## 4. Target Users

### Primary Users

**1. Full-Stack Developers**
- Work across multiple ecosystems (e.g., React + Python API)
- Need unified view of dependency health
- Value time savings from single tool

**2. DevSecOps Engineers**
- Responsible for security compliance
- Require vulnerability reports for audits
- Need SBOM generation for supply chain security

**3. Open Source Maintainers**
- Manage projects with multiple language components
- Need license compliance for contribution guidelines
- Value CI/CD integration for automated checks

### Secondary Users

**4. Security Auditors**
- Reviewing third-party software
- Need comprehensive dependency inventories
- Require industry-standard SBOM formats

**5. Platform/Infra Teams**
- Enforcing organization-wide policies
- Configuring allowed/blocked licenses
- Rolling out security scanning requirements

---

## 5. Core Features

### 5.1 Multi-Language Dependency Scanning (P0)

```bash
depswiz check [--language <lang>] [--path <dir>]
```

| Language | Manifest Files | Lockfiles | Registry |
|----------|---------------|-----------|----------|
| Python | pyproject.toml, requirements.txt, setup.py | uv.lock, poetry.lock, Pipfile.lock | PyPI |
| Rust | Cargo.toml | Cargo.lock | crates.io |
| Dart/Flutter | pubspec.yaml | pubspec.lock | pub.dev |
| JS/TS | package.json | package-lock.json, yarn.lock, pnpm-lock.yaml | npm |

**Behavior:**
- Auto-detect manifest files in current directory (or specified path)
- Parse version constraints from manifests
- Query registry APIs for latest versions
- Compare and report outdated packages
- Classify updates: patch, minor, major

### 5.2 Vulnerability Scanning (P0)

```bash
depswiz audit [--severity <level>] [--ignore <vuln-id>]
```

**Vulnerability Sources:**
- **OSV (Open Source Vulnerabilities)**: Primary source, covers PyPI, npm, crates.io, Go, Maven
- **GitHub Security Advisories**: GHSA identifiers
- **RustSec Advisory Database**: Rust-specific advisories

**Features:**
- Query by package name + version
- Report CVE/GHSA identifiers
- Include severity (CVSS scores where available)
- Provide remediation guidance (fixed versions)
- Support `--fail-on` for CI integration

### 5.3 Plugin Architecture (P0)

```python
# Plugin registration via pyproject.toml
[project.entry-points."depswiz.languages"]
python = "depswiz.plugins.python:PythonPlugin"
rust = "depswiz.plugins.rust:RustPlugin"
```

**Plugin Interface:**
```python
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

class LanguagePlugin(ABC):
    """Base class for language plugins."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin identifier (e.g., 'python', 'rust')."""

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable name for output."""

    @property
    @abstractmethod
    def manifest_patterns(self) -> List[str]:
        """Glob patterns for manifest files."""

    @property
    @abstractmethod
    def lockfile_patterns(self) -> List[str]:
        """Glob patterns for lockfile files."""

    @abstractmethod
    def parse_manifest(self, path: Path) -> List[Package]:
        """Parse manifest file into package list."""

    @abstractmethod
    def parse_lockfile(self, path: Path) -> List[Package]:
        """Parse lockfile into resolved package list."""

    @abstractmethod
    async def fetch_latest_version(self, package: Package) -> Optional[str]:
        """Query registry for latest version."""

    @abstractmethod
    async def fetch_vulnerabilities(self, package: Package) -> List[Vulnerability]:
        """Query vulnerability databases."""

    @abstractmethod
    async def fetch_license(self, package: Package) -> Optional[LicenseInfo]:
        """Fetch license information from registry."""

    @abstractmethod
    def generate_update_command(self, packages: List[Package]) -> List[str]:
        """Generate native update command."""
```

### 5.4 SBOM Generation (P1)

```bash
depswiz sbom [--format cyclonedx|spdx] [--output <file>]
```

**Supported Formats:**
- **CycloneDX 1.6** (JSON/XML): OWASP standard, security-focused
- **SPDX 3.0** (JSON): Linux Foundation standard, license-focused

**SBOM Contents:**
- Package name, version, PURL (Package URL)
- License identifiers (SPDX format)
- Checksums (SHA-256 where available)
- Supplier/author information
- Dependency relationships (direct/transitive)
- Vulnerability references

### 5.5 License Compliance (P1)

```bash
depswiz licenses [--policy <file>] [--fail-on <license>]
```

**Features:**
- Extract license from registry metadata
- Map to SPDX identifiers
- Policy-based enforcement:
  - Allowed licenses (whitelist)
  - Blocked licenses (blacklist)
  - Copyleft detection warnings
- Compatibility matrix warnings

### 5.6 Monorepo Support (P1)

```bash
depswiz check --recursive
depswiz check --workspace
```

**Detection Strategies:**
- **Python**: Look for `src/` layout, multiple pyproject.toml
- **Rust**: Parse `[workspace]` in Cargo.toml
- **JS/TS**: Parse `workspaces` in package.json (npm/yarn/pnpm)
- **Dart**: Parse workspace configuration in pubspec.yaml

**Aggregation:**
- Unified report across all workspace members
- Deduplicated package list with version consistency warnings
- Per-workspace and aggregate vulnerability counts

### 5.7 Multiple Output Formats (P1)

```bash
depswiz check --format <format> --output <file>
```

| Format | Use Case | Details |
|--------|----------|---------|
| `cli` (default) | Interactive terminal | Rich tables, colors, progress bars |
| `json` | CI/CD integration | Structured data for parsing |
| `markdown` | Documentation | GitHub-compatible tables |
| `html` | Reports | Self-contained HTML with styling |
| `cyclonedx` | SBOM export | CycloneDX 1.6 JSON |
| `spdx` | SBOM export | SPDX 3.0 JSON |

### 5.8 Auto-Update with Confirmation (P2)

```bash
depswiz update [--dry-run] [--major|--minor|--patch]
```

**Behavior:**
- Display proposed changes
- Require explicit confirmation (unless `--yes`)
- Generate appropriate update commands per ecosystem
- Optionally execute updates
- Re-run lockfile commands (e.g., `uv lock --upgrade`)

---

## 6. CLI Interface Design

### 6.1 Command Structure

```
depswiz <command> [options]

Commands:
  check      Check for outdated dependencies
  audit      Scan for security vulnerabilities
  licenses   Check license compliance
  sbom       Generate Software Bill of Materials
  update     Update dependencies (with confirmation)
  config     Manage configuration
  plugins    List and manage plugins
  version    Show version information

Global Options:
  --config, -c <file>    Use specific config file
  --verbose, -v          Increase verbosity (repeatable)
  --quiet, -q            Suppress non-essential output
  --no-color             Disable colored output
  --format, -f <format>  Output format: cli, json, markdown, html
  --output, -o <file>    Write output to file
```

### 6.2 Command Examples

#### Check Command

```bash
depswiz check                           # Check current directory
depswiz check --workspace               # Check all workspace members
depswiz check -l python -l rust         # Check only Python and Rust
depswiz check --strategy security       # Only security-related updates
depswiz check --format json -o deps.json
```

#### Audit Command

```bash
depswiz audit                           # Audit current directory
depswiz audit --severity high           # Only high+ severity
depswiz audit --fail-on critical        # Fail CI on critical vulns
depswiz audit --ignore GHSA-xxxx-yyyy   # Ignore specific advisory
```

#### Licenses Command

```bash
depswiz licenses                        # List all licenses
depswiz licenses --summary              # License distribution
depswiz licenses --deny GPL-3.0         # Fail on GPL-3.0
depswiz licenses --policy company.toml  # Use policy file
```

#### SBOM Command

```bash
depswiz sbom -o sbom.json               # CycloneDX JSON
depswiz sbom --format spdx -o sbom.spdx.json
depswiz sbom --include-transitive       # Full dependency tree
```

#### Update Command

```bash
depswiz update                          # Interactive update
depswiz update --dry-run                # Preview changes
depswiz update --strategy patch -y      # Auto-apply patch updates
depswiz update --package requests       # Update specific package
```

---

## 7. Configuration System

### 7.1 Configuration File Location

depswiz looks for configuration in this order:
1. `--config <file>` (command line)
2. `depswiz.toml` (current directory)
3. `pyproject.toml` `[tool.depswiz]` section
4. `~/.config/depswiz/config.toml` (user config)
5. `/etc/depswiz/config.toml` (system config)

### 7.2 Configuration Schema

```toml
# depswiz.toml - Project Configuration

[depswiz]
version = "1.0"
default_format = "cli"
verbose = false
color = true

[languages]
enabled = ["python", "rust", "dart", "javascript"]

[python]
manifest = "pyproject.toml"
lockfile = "uv.lock"
include_dev = true
dependency_groups = ["dependencies", "dev-dependencies"]

[rust]
manifest = "Cargo.toml"
lockfile = "Cargo.lock"

[dart]
manifest = "pubspec.yaml"
lockfile = "pubspec.lock"

[javascript]
manifest = "package.json"
lockfile = "auto"

[check]
recursive = false
workspace = true
strategy = "all"
warn_breaking = true
fail_outdated = false

[audit]
severity_threshold = "low"
fail_on = "high"
sources = ["osv", "ghsa", "rustsec"]

[audit.ignore]
vulnerabilities = []

[licenses]
policy_mode = "allow"
allowed = ["MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC", "MPL-2.0"]
denied = ["GPL-3.0-only", "GPL-3.0-or-later", "AGPL-3.0-only", "AGPL-3.0-or-later"]
warn_copyleft = true
fail_on_unknown = false

[sbom]
format = "cyclonedx"
spec_version = "1.6"
include_dev = false
include_transitive = true

[update]
strategy = "minor"
require_confirmation = true
update_lockfile = true

[monorepo]
auto_detect = true
aggregate_report = true

[cache]
enabled = true
ttl_seconds = 3600
directory = "~/.cache/depswiz"

[network]
timeout_seconds = 30
max_concurrent_requests = 10
retry_count = 3
```

---

## 8. Technical Architecture

### 8.1 Project Structure

```
depswiz/
├── pyproject.toml
├── README.md
├── LICENSE
├── docs/
│   └── PRD.md
├── src/
│   └── depswiz/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli/
│       │   ├── __init__.py
│       │   ├── app.py
│       │   ├── commands/
│       │   │   ├── __init__.py
│       │   │   ├── check.py
│       │   │   ├── audit.py
│       │   │   ├── licenses.py
│       │   │   ├── sbom.py
│       │   │   ├── update.py
│       │   │   └── plugins.py
│       │   └── formatters/
│       │       ├── __init__.py
│       │       ├── cli.py
│       │       ├── json.py
│       │       ├── markdown.py
│       │       └── html.py
│       ├── core/
│       │   ├── __init__.py
│       │   ├── config.py
│       │   ├── models.py
│       │   ├── scanner.py
│       │   ├── version.py
│       │   └── cache.py
│       ├── plugins/
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── registry.py
│       │   ├── python/
│       │   ├── rust/
│       │   ├── dart/
│       │   └── javascript/
│       ├── security/
│       │   ├── __init__.py
│       │   ├── vulnerabilities.py
│       │   ├── sources/
│       │   │   ├── __init__.py
│       │   │   ├── base.py
│       │   │   ├── osv.py
│       │   │   ├── ghsa.py
│       │   │   └── rustsec.py
│       │   └── licenses.py
│       ├── sbom/
│       │   ├── __init__.py
│       │   ├── cyclonedx.py
│       │   └── spdx.py
│       └── monorepo/
│           ├── __init__.py
│           └── detector.py
└── tests/
```

### 8.2 Key Dependencies

```toml
[project]
name = "depswiz"
version = "1.0.0"
requires-python = ">=3.13"

dependencies = [
    "typer>=0.15.0",
    "rich>=13.9.0",
    "httpx>=0.27.0",
    "pyyaml>=6.0.0",
    "packaging>=24.0",
    "semver>=3.0.0",
    "cyclonedx-python-lib>=11.0.0",
    "anyio>=4.0.0",
    "diskcache>=5.6.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=5.0.0",
    "mypy>=1.13.0",
    "ruff>=0.8.0",
]
```

---

## 9. Registry APIs

| Registry | Endpoint | Response |
|----------|----------|----------|
| PyPI | `GET https://pypi.org/pypi/{package}/json` | `{info: {version, license}}` |
| crates.io | `GET https://crates.io/api/v1/crates/{package}` | `{crate: {max_version}}` |
| pub.dev | `GET https://pub.dev/api/packages/{package}` | `{latest: {version}}` |
| npm | `GET https://registry.npmjs.org/{package}` | `{dist-tags: {latest}, license}` |
| OSV | `POST https://api.osv.dev/v1/query` | `{vulns: [...]}` |

---

## 10. Success Metrics

| Metric | Target |
|--------|--------|
| Test coverage | >90% |
| CLI response time (10 packages) | <2 seconds |
| CLI response time (100 packages) | <10 seconds |
| Vulnerability detection accuracy | >99% |
| SBOM compliance | 100% CycloneDX/SPDX valid |

---

## 11. Future Roadmap

### v1.1
- Go, Ruby, PHP plugins
- Dependency graph visualization
- GitHub Actions integration
- Changelog extraction

### v1.2
- Private registry support (Artifactory, Nexus)
- Policy-as-code engine
- Team dashboard (web UI)
- Historical tracking

### v2.0
- AI-powered breaking change prediction
- Automated update PR generation
- Container image scanning
- Real-time monitoring and alerts

---

## Appendix A: Data Models

```python
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from datetime import datetime
from typing import Optional, List

class UpdateType(Enum):
    PATCH = "patch"
    MINOR = "minor"
    MAJOR = "major"

class Severity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"

@dataclass
class Package:
    name: str
    current_version: Optional[str]
    constraint: Optional[str]
    latest_version: Optional[str] = None
    update_type: Optional[UpdateType] = None
    source_file: Optional[Path] = None
    extras: Optional[List[str]] = None
    language: Optional[str] = None

@dataclass
class Vulnerability:
    id: str
    severity: Severity
    cvss_score: Optional[float]
    title: str
    description: str
    affected_versions: str
    fixed_version: Optional[str]
    references: List[str]
    source: str
    published: Optional[datetime] = None

@dataclass
class LicenseInfo:
    spdx_id: Optional[str]
    name: str
    url: Optional[str] = None
    is_osi_approved: bool = False
    is_copyleft: bool = False
```
