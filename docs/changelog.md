# Changelog

All notable changes to depswiz are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- GitHub Pages documentation site
- Comprehensive command reference documentation
- Language-specific guides for Python, Rust, Dart, and JavaScript

## [0.4.0] - 2025-12-27

### Added
- **Interactive Guide** (`depswiz guide`)
  - Full TUI dashboard powered by Textual with real-time health score monitoring
  - Three interaction modes: dashboard (default), wizard, and chat
  - AI-powered suggestions via Claude Code integration
  - Keyboard navigation: `a`=Audit, `u`=Updates, `l`=Licenses, `t`=Tools, `c`=Chat, `s`=AI, `q`=Quit
  - Drill-down screens for detailed vulnerability, update, and license information
  - Health score algorithm (0-100) based on vulnerabilities, outdated deps, and license issues
- **Deprecation Detection** (`depswiz deprecations`)
  - Flutter/Dart deprecation scanning via `dart analyze`
  - Auto-fix support using `dart fix --apply`
  - AI-powered fixing via `--ai-fix` using Claude Code for complex migrations
  - Multiple output formats: CLI, JSON, Markdown, HTML
  - Filtering options: `--fixable-only`, `--package`, `--status`
  - CI integration with `--fail-on deprecated|removal|breaking`
  - Intelligent replacement and package extraction from deprecation messages
- **Guide Module Components**
  - `GuideState` - Reactive state management with subscriptions
  - `ContextManager` - Project context for AI features
  - `WizardEngine` - State machine for guided workflows
  - Custom Textual widgets: HealthScoreWidget, VulnerabilityPanel, UpdatesPanel, LicensePanel, ToolsPanel
  - Six detail screens: AIScreen, AuditScreen, ChatScreen, LicensesScreen, ToolsScreen, UpdatesScreen

### Changed
- Removed placeholder code and "Coming Soon" stubs
- Upgraded Textual integration for smoother TUI experience

### Dependencies
- Added `textual>=0.89.0` (TUI framework)
- Added `inquirerpy>=0.3.4` (interactive prompts)

## [0.3.0] - 2025-12-27

### Added
- **Expanded Test Coverage**
  - Comprehensive CLI command tests for check, audit, and tools commands
  - Unit tests for configuration system, caching, plugin registry, and version utilities
  - 305 passing tests with 48% overall code coverage
  - Key modules now have high coverage: version.py (100%), cache.py (100%), config.py (93%)
- **GHSA Vulnerability Source**
  - GitHub Security Advisories integration for vulnerability scanning
  - GraphQL API support with optional GitHub token for higher rate limits
- **RustSec Vulnerability Source**
  - RustSec Advisory Database integration for Rust packages
  - Local advisory database support
- **Logging Infrastructure**
  - Rich-formatted logging with configurable levels
  - Logging module with Rich handler integration
  - `--verbose` / `-v` global flag for increased output
  - `--quiet` / `-q` global flag for minimal output
  - `--version` / `-V` flag to display version
- **Dogfooding Test Script**
  - Self-testing script at `scripts/dogfood.py`
  - Tests all CLI commands against the project itself
  - Quick mode (`--quick`) skips slow operations

### Fixed
- CLI argument ordering for Typer with `invoke_without_command=True`
- Vulnerability constructor missing `affected_versions` parameter
- ToolVersion.parse() method usage in tests

### Changed
- Improved error handling across plugin implementations
- Enhanced test fixtures for security vulnerability scanning

## [0.2.0] - 2024-12-27

### Added
- **Development Tools Checking** (`depswiz tools`)
  - Support for 15 development tools: Node.js, npm, pnpm, Yarn, Bun, Deno, Python, uv, pip, Rust, Cargo, Dart, Flutter, Go, Docker
  - Auto-detection of relevant tools based on project files
  - Platform-specific update instructions (macOS, Linux, Windows)
  - `--upgrade` option for Claude Code assisted updates
- **AI-Powered Suggestions** (`depswiz suggest`)
  - Claude Code integration for intelligent upgrade recommendations
  - Focus modes: upgrade, security, quick, toolchain
  - Detailed analysis with priority ordering and risk assessment
- Enhanced `depswiz update` with `--ai-suggest` option

### Changed
- Improved version fetching for Yarn Berry and Bun
- Better handling of pip version format (2 and 3-part versions)
- Official API integration for Dart and Flutter version checking

### Fixed
- Yarn Berry tag parsing for `@yarnpkg/cli/X.Y.Z` format
- Bun tag parsing for `bun-vX.Y.Z` format
- pip version regex now handles versions like `24.0`

## [0.1.0] - 2024-12-01

### Added
- Initial release
- **Multi-language dependency checking** (`depswiz check`)
  - Python (pyproject.toml, requirements.txt)
  - Rust (Cargo.toml)
  - Dart/Flutter (pubspec.yaml)
  - JavaScript/TypeScript (package.json)
- **Vulnerability scanning** (`depswiz audit`)
  - OSV integration
  - GitHub Advisory Database
  - RustSec for Rust packages
  - Severity filtering and fail-on thresholds
- **License compliance** (`depswiz licenses`)
  - SPDX-based license detection
  - Allow/deny list support
  - Copyleft warnings
- **SBOM generation** (`depswiz sbom`)
  - CycloneDX 1.6 format
  - SPDX 3.0 format
  - Transitive dependency support
- **Interactive update** (`depswiz update`)
  - Dry-run mode
  - Update strategies (patch, minor, major, security)
  - Auto-confirm option
- **Plugin architecture**
  - Python entry points for language plugins
  - Extensible design
- **Multiple output formats**
  - CLI (Rich tables)
  - JSON
  - Markdown
  - HTML
- **Configuration**
  - depswiz.toml support
  - pyproject.toml [tool.depswiz] section
- **Workspace/monorepo support**
  - Auto-detect workspaces per ecosystem
  - Aggregated reporting

[Unreleased]: https://github.com/moinsen-dev/depswiz/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/moinsen-dev/depswiz/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/moinsen-dev/depswiz/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/moinsen-dev/depswiz/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/moinsen-dev/depswiz/releases/tag/v0.1.0
