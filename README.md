# depswiz

**Dependency Wizard** - A multi-language dependency management CLI tool for modern development workflows.

[![PyPI version](https://img.shields.io/pypi/v/depswiz.svg)](https://pypi.org/project/depswiz/)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/moinsen-dev/depswiz/actions/workflows/ci.yml/badge.svg)](https://github.com/moinsen-dev/depswiz/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/badge/coverage-48%25-yellow)](https://github.com/moinsen-dev/depswiz)
[![Documentation](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://moinsen-dev.github.io/depswiz/)

## Features

- **Multi-Language Support**: Python, Rust, Dart/Flutter, JavaScript/TypeScript
- **Vulnerability Scanning**: Integrated with OSV, GitHub Advisories, RustSec
- **License Compliance**: SPDX-based license checking with configurable policies
- **SBOM Generation**: CycloneDX 1.6 and SPDX 3.0 formats
- **Monorepo Support**: Auto-detect workspaces across all ecosystems
- **Development Tools Checking**: Check if Node, Python, Rust, Dart, Flutter, uv, etc. are up to date
- **Interactive Guide**: TUI dashboard with real-time health monitoring, wizard mode, and AI chat
- **Deprecation Detection**: Scan and auto-fix deprecated API usage (Flutter/Dart)
- **AI-Powered Suggestions**: Claude Code integration for intelligent upgrade strategies
- **Beautiful CLI**: Rich output with tables, progress bars, and colors
- **Plugin Architecture**: Extensible via Python entry points

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
# Check for outdated dependencies
depswiz check

# Scan for vulnerabilities
depswiz audit

# Check license compliance
depswiz licenses

# Generate SBOM
depswiz sbom -o sbom.json

# Update dependencies interactively
depswiz update

# Check development tools for updates
depswiz tools

# Get AI-powered upgrade suggestions (requires Claude Code)
depswiz suggest

# Launch interactive dashboard
depswiz guide

# Scan for deprecated APIs (Flutter/Dart)
depswiz deprecations
```

## Commands

### `depswiz check`

Check dependencies for available updates.

```bash
depswiz check                      # Check current directory
depswiz check --workspace          # Check all workspace members
depswiz check -l python -l rust    # Check only Python and Rust
depswiz check --format json        # Output as JSON
depswiz check --fail-outdated      # Exit 1 if outdated packages found
```

### `depswiz audit`

Scan dependencies for known vulnerabilities.

```bash
depswiz audit                      # Audit current directory
depswiz audit --severity high      # Only show high+ severity
depswiz audit --fail-on critical   # Fail on critical vulnerabilities
depswiz audit --ignore CVE-2024-XXX  # Ignore specific vulnerability
```

### `depswiz licenses`

Check license compliance.

```bash
depswiz licenses                   # List all licenses
depswiz licenses --summary         # License distribution only
depswiz licenses --deny GPL-3.0    # Fail on GPL-3.0 licensed packages
```

### `depswiz sbom`

Generate Software Bill of Materials.

```bash
depswiz sbom -o sbom.json          # CycloneDX format (default)
depswiz sbom --format spdx -o sbom.spdx.json
depswiz sbom --include-transitive  # Include transitive dependencies
```

### `depswiz update`

Update dependencies interactively.

```bash
depswiz update                     # Interactive update
depswiz update --dry-run           # Preview changes
depswiz update --strategy patch    # Only patch updates
depswiz update -y                  # Auto-confirm
```

### `depswiz tools`

Check development tools for updates.

```bash
depswiz tools                      # Auto-detect and check relevant tools
depswiz tools --all                # Check all 15 supported tools
depswiz tools -t node -t python    # Check specific tools
depswiz tools --updates-only       # Only show tools with updates
depswiz tools --format json        # JSON output for CI
depswiz tools --upgrade            # Use Claude Code to upgrade tools
```

**Supported Tools:** Node.js, npm, pnpm, Yarn, Bun, Deno, Python, uv, pip, Rust, Cargo, Dart, Flutter, Go, Docker

### `depswiz suggest`

Get AI-powered upgrade suggestions using Claude Code.

```bash
depswiz suggest                    # Full upgrade strategy
depswiz suggest --focus security   # Focus on security vulnerabilities
depswiz suggest --focus quick      # Quick health summary
depswiz suggest --focus toolchain  # Analyze development tools
```

**Note:** Requires [Claude Code CLI](https://claude.ai/code) to be installed.

### `depswiz guide`

Interactive dependency management dashboard with three modes.

```bash
depswiz guide                      # Launch TUI dashboard
depswiz guide --mode wizard        # Step-by-step guided wizard
depswiz guide --mode chat          # Conversational mode with AI
depswiz guide --watch              # Auto-refresh on file changes
depswiz guide --skip-ai            # Disable AI features
```

**Dashboard Features:**
- Real-time health score (0-100)
- Vulnerability severity breakdown
- Outdated packages by update type
- License compliance status
- Development tools version check

**Keyboard Shortcuts:** `a`=Audit, `u`=Updates, `l`=Licenses, `t`=Tools, `c`=Chat, `s`=AI Suggestions, `q`=Quit

### `depswiz deprecations`

Detect and fix deprecated API usage in Flutter/Dart projects.

```bash
depswiz deprecations               # Scan for deprecations
depswiz deprecations --fix         # Auto-fix using dart fix
depswiz deprecations --dry-run     # Preview fixes without applying
depswiz deprecations --fixable-only  # Show only auto-fixable issues
depswiz deprecations --package flutter  # Filter by package
depswiz deprecations --format json  # JSON output for CI
depswiz deprecations --fail-on breaking  # Exit 1 for breaking deprecations
```

**Supported Detection:**
- `deprecated_member_use` - Standard deprecation warnings
- `deprecated_member_use_from_same_package` - Internal deprecations
- Automatic replacement suggestions extraction
- Source package identification

## Configuration

Create a `depswiz.toml` in your project root:

```toml
[depswiz]
default_format = "cli"

[languages]
enabled = ["python", "rust", "dart", "javascript"]

[check]
recursive = false
workspace = true
strategy = "all"
warn_breaking = true

[audit]
severity_threshold = "low"
fail_on = "high"
sources = ["osv"]

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
fail_on = "high"
```

## Supported Languages

| Language | Manifest | Lockfile | Registry |
|----------|----------|----------|----------|
| Python | pyproject.toml, requirements.txt | uv.lock, poetry.lock | PyPI |
| Rust | Cargo.toml | Cargo.lock | crates.io |
| Dart/Flutter | pubspec.yaml | pubspec.lock | pub.dev |
| JavaScript/TypeScript | package.json | package-lock.json, yarn.lock | npm |

## Output Formats

- **cli** (default): Rich terminal output with colors and tables
- **json**: Machine-readable JSON
- **markdown**: GitHub-compatible markdown
- **html**: Self-contained HTML report
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

## CI/CD Integration

### GitHub Actions

```yaml
- name: Security Audit
  run: depswiz audit --fail-on high

- name: License Check
  run: depswiz licenses --fail-on-unknown

- name: Generate SBOM
  run: depswiz sbom -o sbom.json
```

### Exit Codes

- `0`: Success
- `1`: Vulnerabilities or violations found (when using `--fail-*` options)

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

- [OSV](https://osv.dev/) for vulnerability data
- [CycloneDX](https://cyclonedx.org/) and [SPDX](https://spdx.dev/) for SBOM standards
- [Rich](https://github.com/Textualize/rich), [Typer](https://typer.tiangolo.com/), and [Textual](https://textual.textualize.io/) for beautiful CLI and TUI
- [InquirerPy](https://github.com/kazhala/InquirerPy) for interactive prompts
