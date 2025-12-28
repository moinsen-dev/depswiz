# depswiz

**Dependency Wizard** - One command to check everything. Multi-language dependency management for modern development workflows.

[![PyPI version](https://img.shields.io/pypi/v/depswiz.svg)](https://pypi.org/project/depswiz/)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/moinsen-dev/depswiz/actions/workflows/ci.yml/badge.svg)](https://github.com/moinsen-dev/depswiz/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/badge/coverage-48%25-yellow)](https://github.com/moinsen-dev/depswiz)
[![Documentation](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://moinsen-dev.github.io/depswiz/)

## Why depswiz?

```bash
# Just run depswiz. That's it.
depswiz
```

One command checks your dependencies, scans for vulnerabilities, and validates licenses - across Python, Rust, Dart, JavaScript, Go, and Docker. Zero configuration required.

## Features

- **Zero-Config CI/CD**: Auto-detects CI environments and enables strict mode automatically
- **Multi-Language**: Python, Rust, Dart/Flutter, JavaScript/TypeScript, Go, and Docker
- **Docker Support**: Scan Dockerfiles and Compose files for outdated base images
- **Vulnerability Scanning**: Integrated with OSV, GitHub Advisories, RustSec, NVD
- **License Compliance**: SPDX-based license checking with configurable policies
- **SBOM Generation**: CycloneDX 1.6 and SPDX 3.0 formats
- **SARIF Output**: GitHub Code Scanning and VS Code integration
- **Monorepo Support**: Auto-detect workspaces, recursive scanning by default
- **Development Tools Checking**: Verify Node, Python, Rust, Dart, Flutter, uv, Docker are up to date
- **Interactive Guide**: TUI dashboard with real-time health monitoring
- **Deprecation Detection**: Scan and auto-fix deprecated API usage (Flutter/Dart)
- **AI-Powered Suggestions**: Claude Code integration for intelligent upgrade strategies
- **Beautiful CLI**: Rich output with tables, progress bars, and colors

## Installation

```bash
# Using pip
pip install depswiz

# Using uv (recommended)
uv add depswiz

# From source
git clone https://github.com/moinsen-dev/depswiz.git
cd depswiz
pip install -e .
```

## Quick Start

```bash
# Check everything at once (dependencies + vulnerabilities + licenses)
depswiz

# Or use individual commands
depswiz check       # Check for outdated dependencies
depswiz audit       # Scan for vulnerabilities
depswiz licenses    # Check license compliance
depswiz sbom        # Generate SBOM
depswiz update      # Update dependencies interactively
depswiz tools       # Check development tools
depswiz suggest     # AI-powered suggestions (requires Claude Code)
depswiz guide       # Launch interactive dashboard
depswiz deprecations  # Scan for deprecated APIs (Flutter/Dart)
```

## Commands

### `depswiz` (Comprehensive Scan)

Run with no arguments to check everything at once.

```bash
depswiz                    # Full scan: deps + vulns + licenses
depswiz --json             # JSON output for parsing
depswiz --strict           # Fail if any issues found
depswiz --only python      # Scan only Python projects
```

### `depswiz check`

Check dependencies for available updates.

```bash
depswiz check                    # Recursive scan (default)
depswiz check --shallow          # Current directory only
depswiz check --json             # JSON output
depswiz check --strict           # Exit 1 if outdated found
depswiz check --only python,rust # Filter by language
depswiz check --prod             # Exclude dev dependencies
```

### `depswiz audit`

Scan dependencies for known vulnerabilities.

```bash
depswiz audit                    # Scan all vulnerabilities
depswiz audit --strict           # Fail on any vulnerability
depswiz audit --strict critical  # Fail only on critical
depswiz audit --ignore CVE-2024-XXX  # Ignore specific CVE
depswiz audit --sarif -o results.sarif  # SARIF for GitHub Code Scanning
```

### `depswiz licenses`

Check license compliance.

```bash
depswiz licenses                 # List all licenses
depswiz licenses --summary       # License distribution only
depswiz licenses --strict        # Fail on violations
depswiz licenses --deny GPL-3.0  # Deny specific licenses
```

### `depswiz sbom`

Generate Software Bill of Materials.

```bash
depswiz sbom -o sbom.json        # CycloneDX format (default)
depswiz sbom --spdx -o sbom.spdx.json  # SPDX format
depswiz sbom --dev               # Include dev dependencies
```

### `depswiz update`

Update dependencies interactively.

```bash
depswiz update                   # Interactive update
depswiz update --dry-run         # Preview changes only
depswiz update --strategy patch  # Only patch updates
depswiz update -y                # Auto-confirm all
```

### `depswiz tools`

Check development tools for updates.

```bash
depswiz tools                    # Check relevant tools
depswiz tools --all              # Check all 15 supported tools
depswiz tools --updates-only     # Only show outdated
depswiz tools --upgrade          # Use Claude Code to upgrade
```

**Supported Tools:** Node.js, npm, pnpm, Yarn, Bun, Deno, Python, uv, pip, Rust, Cargo, Dart, Flutter, Go, Docker

### `depswiz suggest`

Get AI-powered upgrade suggestions using Claude Code.

```bash
depswiz suggest                  # Full upgrade strategy
depswiz suggest --focus security # Focus on vulnerabilities
depswiz suggest --focus quick    # Quick health summary
```

**Note:** Requires [Claude Code CLI](https://claude.ai/code) to be installed.

### `depswiz guide`

Interactive dependency management dashboard.

```bash
depswiz guide                    # Launch TUI dashboard
depswiz guide --mode wizard      # Step-by-step wizard
depswiz guide --mode chat        # Conversational mode
```

**Keyboard Shortcuts:** `a`=Audit, `u`=Updates, `l`=Licenses, `t`=Tools, `c`=Chat, `s`=AI, `q`=Quit

### `depswiz deprecations`

Detect and fix deprecated API usage in Flutter/Dart projects.

```bash
depswiz deprecations             # Scan for deprecations
depswiz deprecations --fix       # Auto-fix with dart fix
depswiz deprecations --ai-fix    # AI-powered complex fixes
depswiz deprecations --fixable-only  # Show only auto-fixable
```

## CI/CD Integration

### Zero-Configuration

depswiz automatically detects CI environments and adjusts its behavior:

- **Auto-strict mode**: Fails build on issues (no flags needed)
- **Auto-JSON output**: Machine-readable output by default
- **Recursive scanning**: Checks entire project tree

**Detected Platforms:** GitHub Actions, GitLab CI, CircleCI, Travis CI, Jenkins, Azure Pipelines, Bitbucket Pipelines, TeamCity, Buildkite, Drone, Woodpecker, Codeship, Semaphore

### GitHub Actions

```yaml
name: Security Check
on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.13'
      - run: pip install depswiz
      - run: depswiz  # That's it! Strict mode auto-enabled
```

### Exit Codes

- `0`: Success - no issues found
- `1`: Issues found (with `--strict` or auto-enabled in CI)

## Configuration

Create a `depswiz.toml` in your project root:

```toml
[depswiz]
default_format = "cli"

[languages]
enabled = ["python", "rust", "dart", "javascript", "golang", "docker"]

[check]
recursive = true
warn_breaking = true

[audit]
severity_threshold = "low"
sources = ["osv", "ghsa", "rustsec", "nvd"]

[licenses]
policy_mode = "allow"
allowed = ["MIT", "Apache-2.0", "BSD-3-Clause", "ISC"]
denied = ["GPL-3.0", "AGPL-3.0"]
warn_copyleft = true

[sbom]
format = "cyclonedx"
include_transitive = true
```

Or add to your `pyproject.toml`:

```toml
[tool.depswiz]
default_format = "cli"

[tool.depswiz.audit]
severity_threshold = "high"
```

## Supported Languages

| Language | Manifest Files | Lockfiles | Registry |
|----------|---------------|-----------|----------|
| Python | pyproject.toml, requirements.txt | uv.lock, poetry.lock | PyPI |
| Rust | Cargo.toml | Cargo.lock | crates.io |
| Dart/Flutter | pubspec.yaml | pubspec.lock | pub.dev |
| JavaScript/TypeScript | package.json | package-lock.json, yarn.lock | npm |
| Go | go.mod | go.sum | Go Module Proxy |
| Docker | Dockerfile, docker-compose.yml | - | Docker Hub |

## Output Formats

- **cli** (default): Rich terminal output with colors and tables
- **json**: Machine-readable JSON (`--json`)
- **markdown**: GitHub-compatible markdown (`--md`)
- **html**: Self-contained HTML report (`--html`)
- **sarif**: SARIF 2.1 for GitHub Code Scanning and VS Code (`--sarif`)
- **cyclonedx**: CycloneDX 1.6 SBOM
- **spdx**: SPDX 3.0 SBOM

## Plugin Development

Create a new language plugin by implementing `LanguagePlugin`:

```python
from depswiz.plugins.base import LanguagePlugin

class MyPlugin(LanguagePlugin):
    @property
    def name(self) -> str:
        return "mylang"

    @property
    def manifest_patterns(self) -> list[str]:
        return ["myproject.toml"]

    # ... implement other required methods
```

Register via `pyproject.toml`:

```toml
[project.entry-points."depswiz.languages"]
mylang = "my_package:MyPlugin"
```

## Development

```bash
# Clone and install
git clone https://github.com/moinsen-dev/depswiz.git
cd depswiz
pip install -e ".[dev]"

# Run tests
pytest

# Run dogfooding tests (depswiz checks itself)
python scripts/dogfood.py
python scripts/dogfood.py --quick  # Skip slow operations

# Type checking
mypy src/depswiz

# Linting
ruff check src/depswiz
```

## Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- [OSV](https://osv.dev/), [NVD](https://nvd.nist.gov/), and [GitHub Advisories](https://github.com/advisories) for vulnerability data
- [CycloneDX](https://cyclonedx.org/) and [SPDX](https://spdx.dev/) for SBOM standards
- [SARIF](https://sarifweb.azurewebsites.net/) for static analysis result format
- [Rich](https://github.com/Textualize/rich), [Typer](https://typer.tiangolo.com/), and [Textual](https://textual.textualize.io/) for beautiful CLI and TUI
- [InquirerPy](https://github.com/kazhala/InquirerPy) for interactive prompts
